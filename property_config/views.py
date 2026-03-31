from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.views import View
import json
from django.utils.safestring import mark_safe
from properties.models import Property
from .models import PropertyConfig
from .serializers import PropertyConfigSerializer
from .services.property_evaluator import PropertyEvaluationService
from .services.property_diagnosis import PropertyDiagnosisService


class PropertyConfigViewSet(viewsets.ModelViewSet):
    queryset = PropertyConfig.objects.all()
    serializer_class = PropertyConfigSerializer


@api_view(['GET'])
def property_evaluation_view(request, property_id, month):
    """
    Evaluate property performance for a given month (JSON API).
    
    GET /api/property-evaluation/<property_id>/<month>/
    
    Args:
        property_id: Property ID
        month: Month in format YYYY-MM
    
    Returns:
        JSON with evaluation metrics, KPIs, forecast, and validation.
    """
    try:
        # Get property
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Get evaluation service and evaluate
        service = PropertyEvaluationService.for_property_month(property_obj, month)
        evaluation_data = service.evaluate()
        
        # Restructure response for UI
        response_data = {
            'property': {
                'id': evaluation_data['property_id'],
                'name': evaluation_data['property_name'],
            },
            'month': evaluation_data['month'],
            'month_progress': evaluation_data['current_day'] / evaluation_data['days_in_month'],
            'current_day': evaluation_data['current_day'],
            'days_in_month': evaluation_data['days_in_month'],
            'rooms': evaluation_data['rooms'],
            
            # Actual Performance
            'actual': {
                'nights_to_date': evaluation_data['actual_nights_td'],
                'revenue_to_date': evaluation_data['actual_revenue_td'],
                'adr': evaluation_data['actual_adr'],
            },
            
            # OTB (On The Books)
            'otb': {
                'nights': evaluation_data['otb_nights'],
                'revenue': evaluation_data['otb_revenue'],
            },
            
            # Expected Metrics
            'expected': {
                'adr': evaluation_data['expected_adr'],
                'occupancy': evaluation_data['expected_occupancy'],
                'nights_month': evaluation_data['expected_nights_month'],
                'revenue_month': evaluation_data['expected_revenue_month'],
                'nights_to_date': evaluation_data['expected_nights_td'],
                'revenue_to_date': evaluation_data['expected_revenue_td'],
            },
            
            # KPIs
            'kpis': {
                'pace_ratio': {
                    'value': evaluation_data['pace_ratio'],
                    'threshold': float(service.config.pace_threshold),
                    'status': 'OK' if evaluation_data['pace_ratio_vs_threshold'] else 'BELOW_THRESHOLD',
                },
                'nights_pace_ratio': {
                    'value': evaluation_data['nights_pace_ratio'],
                    'low_threshold': float(service.config.nights_low_threshold),
                    'high_threshold': float(service.config.nights_high_threshold),
                    'status': 'OK' if (evaluation_data['nights_pace_vs_low'] and evaluation_data['nights_pace_vs_high']) else 'OUT_OF_RANGE',
                },
                'adr_ratio': {
                    'value': evaluation_data['adr_ratio'],
                    'low_threshold': float(service.config.adr_low_threshold),
                    'high_threshold': float(service.config.adr_high_threshold),
                    'status': 'OK' if (evaluation_data['adr_vs_low'] and evaluation_data['adr_vs_high']) else 'OUT_OF_RANGE',
                },
                'adr_gap': evaluation_data['adr_gap'],
            },
            
            # Forecast & Potential
            'forecast': {
                'forecast_revenue': evaluation_data['forecast_revenue'],
                'potential_revenue': evaluation_data['potential_revenue'],
                'remaining_free_days': evaluation_data['remaining_free_days'],
                'forecast_vs_target': evaluation_data['forecast_vs_target'],
                'forecast_vs_target_pct': evaluation_data['forecast_vs_target_pct'],
            },
            
            # Data Validation
            'data_validation': {
                'has_revenue_data': evaluation_data['has_revenue_data'],
                'has_nights_data': evaluation_data['has_nights_data'],
                'is_valid': 'VALID' if evaluation_data['data_valid'] else 'INVALID',
            },
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error evaluating property: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class PropertyEvaluationTemplateView(View):
    """HTML template view for property evaluation."""
    
    def get(self, request, property_id, month):
        """Render evaluation results in HTML."""
        try:
            # Get property
            property_obj = get_object_or_404(Property, id=property_id)
            
            # Get evaluation service and evaluate
            service = PropertyEvaluationService.for_property_month(property_obj, month)
            evaluation_data = service.evaluate()
            
            # Prepare context for template
            context = {
                'property': {
                    'id': evaluation_data['property_id'],
                    'name': evaluation_data['property_name'],
                },
                'month': evaluation_data['month'],
                'month_progress_pct': (evaluation_data['current_day'] / evaluation_data['days_in_month']) * 100,
                'current_day': evaluation_data['current_day'],
                'days_in_month': evaluation_data['days_in_month'],
                'rooms': evaluation_data['rooms'],
                
                # Actual Performance
                'actual': {
                    'nights_to_date': evaluation_data['actual_nights_td'],
                    'revenue_to_date': evaluation_data['actual_revenue_td'],
                    'adr': evaluation_data['actual_adr'],
                },
                
                # OTB
                'otb': {
                    'nights': evaluation_data['otb_nights'],
                    'revenue': evaluation_data['otb_revenue'],
                },
                
                # Expected
                'expected': {
                    'adr': evaluation_data['expected_adr'],
                    'occupancy': evaluation_data['expected_occupancy'] * 100,
                    'nights_month': evaluation_data['expected_nights_month'],
                    'revenue_month': evaluation_data['expected_revenue_month'],
                    'nights_to_date': evaluation_data['expected_nights_td'],
                    'revenue_to_date': evaluation_data['expected_revenue_td'],
                },
                
                # KPIs
                'kpis': {
                    'pace_ratio': {
                        'value': evaluation_data['pace_ratio'],
                        'threshold': float(service.config.pace_threshold),
                        'status': 'OK' if evaluation_data['pace_ratio_vs_threshold'] else 'BELOW_THRESHOLD',
                    },
                    'nights_pace_ratio': {
                        'value': evaluation_data['nights_pace_ratio'],
                        'low_threshold': float(service.config.nights_low_threshold),
                        'high_threshold': float(service.config.nights_high_threshold),
                        'status': 'OK' if (evaluation_data['nights_pace_vs_low'] and evaluation_data['nights_pace_vs_high']) else 'OUT_OF_RANGE',
                    },
                    'adr_ratio': {
                        'value': evaluation_data['adr_ratio'],
                        'low_threshold': float(service.config.adr_low_threshold),
                        'high_threshold': float(service.config.adr_high_threshold),
                        'status': 'OK' if (evaluation_data['adr_vs_low'] and evaluation_data['adr_vs_high']) else 'OUT_OF_RANGE',
                    },
                    'adr_gap': evaluation_data['adr_gap'],
                },
                
                # Forecast
                'forecast': {
                    'forecast_revenue': evaluation_data['forecast_revenue'],
                    'potential_revenue': evaluation_data['potential_revenue'],
                    'remaining_free_days': evaluation_data['remaining_free_days'],
                    'forecast_vs_target': evaluation_data['forecast_vs_target'],
                    'forecast_vs_target_pct': evaluation_data['forecast_vs_target_pct'],
                },
                
                # Validation
                'data_validation': {
                    'has_revenue_data': evaluation_data['has_revenue_data'],
                    'has_nights_data': evaluation_data['has_nights_data'],
                    'is_valid': 'VALID' if evaluation_data['data_valid'] else 'INVALID',
                },
            }
            
            # JSON Data for display
            json_context = {
                'property': {
                    'id': evaluation_data['property_id'],
                    'name': evaluation_data['property_name'],
                },
                'month': evaluation_data['month'],
                'month_progress': evaluation_data['current_day'] / evaluation_data['days_in_month'],
                'current_day': evaluation_data['current_day'],
                'days_in_month': evaluation_data['days_in_month'],
                'rooms': evaluation_data['rooms'],
                'actual': {
                    'nights_to_date': evaluation_data['actual_nights_td'],
                    'revenue_to_date': float(evaluation_data['actual_revenue_td']),
                    'adr': float(evaluation_data['actual_adr']),
                },
                'otb': {
                    'nights': evaluation_data['otb_nights'],
                    'revenue': float(evaluation_data['otb_revenue']),
                },
                'expected': {
                    'adr': float(evaluation_data['expected_adr']),
                    'occupancy': float(evaluation_data['expected_occupancy']),
                    'nights_month': evaluation_data['expected_nights_month'],
                    'revenue_month': float(evaluation_data['expected_revenue_month']),
                    'nights_to_date': evaluation_data['expected_nights_td'],
                    'revenue_to_date': float(evaluation_data['expected_revenue_td']),
                },
                'kpis': {
                    'pace_ratio': {
                        'value': float(evaluation_data['pace_ratio']),
                        'threshold': float(service.config.pace_threshold),
                    },
                    'nights_pace_ratio': {
                        'value': float(evaluation_data['nights_pace_ratio']),
                        'low_threshold': float(service.config.nights_low_threshold),
                        'high_threshold': float(service.config.nights_high_threshold),
                    },
                    'adr_ratio': {
                        'value': float(evaluation_data['adr_ratio']),
                        'low_threshold': float(service.config.adr_low_threshold),
                        'high_threshold': float(service.config.adr_high_threshold),
                    },
                    'adr_gap': float(evaluation_data['adr_gap']),
                },
                'forecast': {
                    'forecast_revenue': float(evaluation_data['forecast_revenue']),
                    'potential_revenue': float(evaluation_data['potential_revenue']),
                    'remaining_free_days': evaluation_data['remaining_free_days'],
                    'forecast_vs_target': float(evaluation_data['forecast_vs_target']),
                    'forecast_vs_target_pct': float(evaluation_data['forecast_vs_target_pct']),
                },
                'data_validation': {
                    'has_revenue_data': evaluation_data['has_revenue_data'],
                    'has_nights_data': evaluation_data['has_nights_data'],
                    'is_valid': evaluation_data['data_valid'],
                },
            }
            context['json_data'] = mark_safe(json.dumps(json_context, indent=2))
            
            return render(request, 'property_config/property_evaluation.html', context)
        
        except ValueError as e:
            return render(request, 'property_config/error.html', {'error': str(e)}, status=404)
        except Exception as e:
            return render(request, 'property_config/error.html', {'error': f'Error evaluating property: {str(e)}'}, status=500)


@api_view(['GET'])
def property_diagnosis_view(request, property_id, month):
    """
    Get property diagnosis and recommended actions for a given month (JSON API).
    
    GET /api/property-diagnosis/<property_id>/<month>/
    
    Args:
        property_id: Property ID
        month: Month in format YYYY-MM
    
    Returns:
        JSON with diagnosis status, reason, recommended action, and impact analysis.
    """
    try:
        # Get property
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Get diagnosis service and diagnose
        service = PropertyDiagnosisService(property_obj, month)
        diagnosis_data = service.diagnose()
        
        return Response(diagnosis_data, status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error diagnosing property: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class PropertyDiagnosisTemplateView(View):
    """HTML template view for property diagnosis."""
    
    def get(self, request, property_id, month):
        """Render diagnosis results in HTML."""
        try:
            # Get property
            property_obj = get_object_or_404(Property, id=property_id)
            
            # Get diagnosis service and diagnose
            service = PropertyDiagnosisService(property_obj, month)
            diagnosis_data = service.diagnose()
            
            # Map diagnosis status to visual colors
            status_map = {
                'ON_TRACK': {
                    'icon': '✓',
                    'from': '#28a745',
                    'to': '#20c997',
                    'color': '#28a745',
                },
                'UNDERPRICED': {
                    'icon': '📈',
                    'from': '#ffc107',
                    'to': '#ffb703',
                    'color': '#ffc107',
                },
                'PRICE_TOO_HIGH': {
                    'icon': '📉',
                    'from': '#fd7e14',
                    'to': '#ff6b35',
                    'color': '#fd7e14',
                },
                'LOW_BOOKING_PACE': {
                    'icon': '⚠️',
                    'from': '#ff6b6b',
                    'to': '#ee5a6f',
                    'color': '#ff6b6b',
                },
                'ADR_TOO_LOW': {
                    'icon': '💰',
                    'from': '#ffc107',
                    'to': '#ffb703',
                    'color': '#ffc107',
                },
                'ADR_TOO_HIGH': {
                    'icon': '📊',
                    'from': '#fd7e14',
                    'to': '#ff6b35',
                    'color': '#fd7e14',
                },
                'UNDERPERFORMING': {
                    'icon': '🔍',
                    'from': '#6c757d',
                    'to': '#5a6268',
                    'color': '#6c757d',
                },
                'EARLY_MONTH': {
                    'icon': '⏳',
                    'from': '#17a2b8',
                    'to': '#138496',
                    'color': '#17a2b8',
                },
                'NO_DATA': {
                    'icon': '❌',
                    'from': '#dc3545',
                    'to': '#c82333',
                    'color': '#dc3545',
                },
                'REVIEW_NEEDED': {
                    'icon': '❓',
                    'from': '#6f42c1',
                    'to': '#5a32a3',
                    'color': '#6f42c1',
                },
            }
            
            status_info = status_map.get(diagnosis_data['diagnosis']['status'], status_map['REVIEW_NEEDED'])
            
            # Prepare context
            context = {
                'property': {
                    'id': diagnosis_data['property']['id'],
                    'name': diagnosis_data['property']['name'],
                },
                'month': diagnosis_data['month'],
                'month_progress_pct': (diagnosis_data['data_assessment']['month_progress'] * 100),
                'rooms': diagnosis_data.get('rooms', 1),
                
                # Diagnosis
                'diagnosis': diagnosis_data['diagnosis'],
                'status_icon': status_info['icon'],
                'status_bg_from': status_info['from'],
                'status_bg_to': status_info['to'],
                'status_color': status_info['color'],
                
                # Key Metrics
                'key_metrics': diagnosis_data['key_metrics'],
                'current_adr': diagnosis_data['key_metrics'].get('adr_ratio', {}).get('value', 0),
                'expected_occupancy': diagnosis_data['data_assessment'].get('month_progress', 0),
                
                # Forecast
                'forecast': diagnosis_data['forecast'],
                'remaining_free_days': diagnosis_data.get('remaining_free_days', 0),
                
                # Action Value
                'action_value': diagnosis_data['action_value'],
                
                # Diagnosis Reference
                'diagnosis_reference': diagnosis_data['diagnosis_reference'],
            }
            
            # JSON Data for display
            json_context = {
                'property': diagnosis_data['property'],
                'month': diagnosis_data['month'],
                'diagnosis': diagnosis_data['diagnosis'],
                'key_metrics': diagnosis_data['key_metrics'],
                'data_assessment': diagnosis_data['data_assessment'],
                'forecast': diagnosis_data['forecast'],
                'action_value': diagnosis_data['action_value'],
                'diagnosis_reference': diagnosis_data['diagnosis_reference'],
            }
            context['json_data'] = mark_safe(json.dumps(json_context, indent=2))
            
            return render(request, 'property_config/property_diagnosis.html', context)
        
        except ValueError as e:
            return render(request, 'property_config/error.html', {'error': str(e)}, status=404)
        except Exception as e:
            return render(request, 'property_config/error.html', {'error': f'Error diagnosing property: {str(e)}'}, status=500)


