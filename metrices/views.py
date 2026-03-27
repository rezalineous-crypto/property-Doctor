import csv
import io
from datetime import datetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.db import transaction
from properties.models import Property
from .models import PropertyMetrics
from .serializers import PropertyMetricsSerializer


class PropertyMetricsImportView(APIView):
    """
    API endpoint to import PropertyMetrics from CSV file.
    
    Expected CSV columns:
    - property_name: Name of the property (must exist in database)
    - month: Month in YYYY-MM format
    - revenue: Revenue amount (decimal)
    - occupancy: Occupancy percentage (0-100)
    - bookings: Number of bookings (integer)
    - expenses: Expenses amount (decimal)
    """
    parser_classes = [MultiPartParser]
    
    def post(self, request):
        # Try to get file from different sources
        csv_file = None
        
        # Check request.FILES
        if request.FILES:
            csv_file = request.FILES.get('file')
        # Check request.data (for form-data or JSON with base64)
        elif hasattr(request, 'data') and request.data:
            csv_file = request.data.get('file')
        
        if not csv_file:
            # Debug: show what's available
            return Response(
                {
                    'error': 'No file provided',
                    'debug': {
                        'FILES_keys': list(request.FILES.keys()) if request.FILES else [],
                        'data_keys': list(request.data.keys()) if hasattr(request, 'data') and request.data else []
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        if not csv_file.name.endswith('.csv'):
            return Response(
                {'error': 'File must be a CSV file'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decode and parse CSV
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            
            # Validate required columns
            required_columns = ['property_name', 'month', 'revenue', 'occupancy', 'bookings', 'expenses']
            if not all(col in csv_reader.fieldnames for col in required_columns):
                return Response(
                    {'error': f'CSV must contain columns: {required_columns}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process rows
            results = {
                'created': 0,
                'updated': 0,
                'errors': []
            }
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):  # start=2 accounts for header
                    try:
                        # Map property_name to Property
                        property_name = row['property_name'].strip()
                        try:
                            property_obj = Property.objects.get(name=property_name)
                        except Property.DoesNotExist:
                            results['errors'].append({
                                'row': row_num,
                                'error': f"Property '{property_name}' not found"
                            })
                            continue
                        
                        # Parse month (YYYY-MM format)
                        month_str = row['month'].strip()
                        try:
                            month_date = datetime.strptime(month_str, '%Y-%m').date()
                        except ValueError:
                            results['errors'].append({
                                'row': row_num,
                                'error': f"Invalid month format '{month_str}'. Expected YYYY-MM"
                            })
                            continue
                        
                        # Parse numeric fields
                        try:
                            revenue = float(row['revenue']) if row['revenue'] else 0
                            occupancy = float(row['occupancy']) if row['occupancy'] else 0
                            bookings = int(row['bookings']) if row['bookings'] else 0
                            expenses = float(row['expenses']) if row['expenses'] else 0
                        except ValueError as e:
                            results['errors'].append({
                                'row': row_num,
                                'error': f"Invalid numeric value: {str(e)}"
                            })
                            continue
                        
                        # Validate occupancy range
                        if occupancy < 0 or occupancy > 100:
                            results['errors'].append({
                                'row': row_num,
                                'error': f"Occupancy must be between 0 and 100, got {occupancy}"
                            })
                            continue
                        
                        # Check if metrics already exists for this property and month
                        metrics, created = PropertyMetrics.objects.update_or_create(
                            property=property_obj,
                            month=month_date,
                            defaults={
                                'revenue': revenue,
                                'occupancy': occupancy,
                                'bookings': bookings,
                                'expenses': expenses,
                            }
                        )
                        
                        if created:
                            results['created'] += 1
                        else:
                            results['updated'] += 1
                            
                    except Exception as e:
                        results['errors'].append({
                            'row': row_num,
                            'error': str(e)
                        })
            
            # Return success response
            if results['errors']:
                return Response({
                    'status': 'completed_with_errors',
                    'message': f"Imported {results['created']} new, updated {results['updated']} existing records",
                    'results': results
                }, status=status.HTTP_207_MULTI_STATUS)
            
            return Response({
                'status': 'success',
                'message': f"Successfully imported {results['created']} new, updated {results['updated']} existing records",
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to process CSV: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
