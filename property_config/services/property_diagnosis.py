from decimal import Decimal
from property_config.services.property_evaluator import PropertyEvaluationService


class PropertyDiagnosisService:
    """
    Diagnostic service that analyzes property performance and recommends actions.
    
    Takes PropertyEvaluationService output and applies a rule-based diagnosis
    to determine status, reasoning, and specific actions with calculated outcomes.
    """
    
    # Diagnosis reference rules
    DIAGNOSIS_RULES = {
        'on_track': {
            'condition': 'Pace ≥ 0.95',
            'description': 'Revenue pace is meeting or exceeding target',
            'action': 'No change - monitor',
        },
        'underpriced': {
            'condition': 'Pace ≥ 0.95, Nights ≥ 1.05, ADR < 0.90',
            'description': 'Strong demand but ADR is too low - opportunity to increase price',
            'action': 'Increase ADR 5-10%',
        },
        'price_too_high': {
            'condition': 'Pace < 0.95, Nights < 0.90, ADR > 1.15',
            'description': 'Both demand and ADR are weak - competitive pricing needed',
            'action': 'Reduce ADR 10-15%',
        },
        'low_booking_pace': {
            'condition': 'Pace < 0.95, Nights < 0.90, ADR ≤ 1.15',
            'description': 'Low booking pace with fair pricing - need visibility or promotions',
            'action': 'Increase visibility + limited discount 5-10%',
        },
        'adr_too_low': {
            'condition': 'Pace < 0.95, Nights ≥ 0.90, ADR < 0.90',
            'description': 'Good demand but leaving money on table with low ADR',
            'action': 'Increase ADR 5-10%',
        },
        'adr_too_high': {
            'condition': 'Pace < 0.95, Nights ≥ 0.90, ADR > 1.15',
            'description': 'Booking pace weak despite meeting occupancy - ADR is too high',
            'action': 'Reduce ADR 5-10%',
        },
        'underperforming': {
            'condition': 'Pace < 0.95, Nights ≥ 0.90, ADR 0.90-1.15',
            'description': 'Performance is underperforming with balanced metrics - full review needed',
            'action': 'Conduct full market review',
        },
        'early_month': {
            'condition': 'Month progress < 10%',
            'description': 'Too early to diagnose - wait for sufficient data',
            'action': 'Monitor and reassess in 3-5 days',
        },
        'no_data': {
            'condition': 'No revenue or nights data',
            'description': 'Insufficient data to diagnose',
            'action': 'Gather more data - activate listing if needed',
        },
    }
    
    def __init__(self, property_obj, month):
        """
        Initialize diagnosis service.
        
        Args:
            property_obj: Property instance
            month: String in format "YYYY-MM"
        """
        self.property = property_obj
        self.month = month
        self.evaluation_service = PropertyEvaluationService.for_property_month(property_obj, month)
        self.evaluation_data = self.evaluation_service.evaluate()
    
    def diagnose(self):
        """
        Run full diagnosis and return structured diagnosis report.
        
        Returns:
            Dictionary with status, reason, action, metrics, forecast, and action values.
        """
        # Extract key metrics
        pace_ratio = self.evaluation_data['pace_ratio']
        nights_pace = self.evaluation_data['nights_pace_ratio']
        adr_ratio = self.evaluation_data['adr_ratio']
        adr_gap = self.evaluation_data['adr_gap']
        data_valid = self.evaluation_data['data_valid']
        month_progress = self.evaluation_data['current_day'] / self.evaluation_data['days_in_month']
        
        # Determine diagnosis
        status, reason, action_type, action_desc = self._apply_diagnosis_rules(
            pace_ratio, nights_pace, adr_ratio, adr_gap, data_valid, month_progress
        )
        
        # Calculate action values
        action_value = self._calculate_action_value(action_type, adr_ratio)
        
        # Build comprehensive response
        return {
            'property': {
                'id': self.evaluation_data['property_id'],
                'name': self.evaluation_data['property_name'],
            },
            'month': self.month,
            'diagnosis': {
                'status': status,
                'reason': reason,
                'action': action_desc,
                'action_type': action_type,
            },
            'key_metrics': {
                'pace_ratio': {
                    'value': pace_ratio,
                    'threshold': float(self.evaluation_service.config.pace_threshold),
                    'status': 'GOOD' if pace_ratio >= float(self.evaluation_service.config.pace_threshold) else 'WEAK',
                },
                'nights_pace_ratio': {
                    'value': nights_pace,
                    'low_threshold': float(self.evaluation_service.config.nights_low_threshold),
                    'high_threshold': float(self.evaluation_service.config.nights_high_threshold),
                    'status': 'OK' if (nights_pace >= float(self.evaluation_service.config.nights_low_threshold) and nights_pace <= float(self.evaluation_service.config.nights_high_threshold)) else 'OUT_OF_RANGE',
                },
                'adr_ratio': {
                    'value': adr_ratio,
                    'low_threshold': float(self.evaluation_service.config.adr_low_threshold),
                    'high_threshold': float(self.evaluation_service.config.adr_high_threshold),
                },
                'adr_gap': {
                    'value': adr_gap,
                    'interpretation': 'Above expected' if adr_gap > 0 else 'Below expected',
                },
            },
            'forecast': {
                'target_revenue': self.evaluation_data['expected_revenue_month'],
                'forecast_revenue': self.evaluation_data['forecast_revenue'],
                'potential_revenue': self.evaluation_data['potential_revenue'],
                'forecast_vs_target': self.evaluation_data['forecast_vs_target'],
                'forecast_vs_target_pct': self.evaluation_data['forecast_vs_target_pct'],
            },
            'action_value': action_value,
            'data_assessment': {
                'has_revenue_data': self.evaluation_data['has_revenue_data'],
                'has_nights_data': self.evaluation_data['has_nights_data'],
                'is_valid': self.evaluation_data['data_valid'],
                'month_progress': month_progress,
            },
            'diagnosis_reference': self.DIAGNOSIS_RULES,
        }
    
    def _apply_diagnosis_rules(self, pace_ratio, nights_pace, adr_ratio, adr_gap, data_valid, month_progress):
        """
        Apply diagnosis rules to determine status and action.
        
        Args:
            pace_ratio: Revenue pace (actual / expected)
            nights_pace: Nights pace (actual / expected)
            adr_ratio: ADR ratio (actual / expected)
            adr_gap: ADR gap (actual - expected)
            data_valid: Whether data is valid
            month_progress: Progress through month (0-1)
        
        Returns:
            Tuple of (status, reason, action_type, action_description)
        """
        # Data validation checks
        if not data_valid:
            return 'NO_DATA', 'No revenue or nights data available', 'gather_data', self.DIAGNOSIS_RULES['no_data']['action']
        
        # Early month check (less than 10% progress)
        if month_progress < 0.10:
            return 'EARLY_MONTH', 'Too early in month to make reliable diagnosis', 'monitor', self.DIAGNOSIS_RULES['early_month']['action']
        
        # Rule 1: On Track (Pace ≥ 0.95)
        if pace_ratio >= 0.95:
            return 'ON_TRACK', self.DIAGNOSIS_RULES['on_track']['description'], 'no_action', 'Monitor performance - no immediate action needed'
        
        # Rule 2: Underpriced (Pace ≥ 0.95, Nights ≥ 1.05, ADR < 0.90)
        if pace_ratio >= 0.95 and nights_pace >= 1.05 and adr_ratio < 0.90:
            return 'UNDERPRICED', self.DIAGNOSIS_RULES['underpriced']['description'], 'raise_adr', self.DIAGNOSIS_RULES['underpriced']['action']
        
        # Rule 3: Price Too High (Pace < 0.95, Nights < 0.90, ADR > 1.15)
        if pace_ratio < 0.95 and nights_pace < 0.90 and adr_ratio > 1.15:
            return 'PRICE_TOO_HIGH', self.DIAGNOSIS_RULES['price_too_high']['description'], 'reduce_adr_aggressive', self.DIAGNOSIS_RULES['price_too_high']['action']
        
        # Rule 4: Low Booking Pace (Pace < 0.95, Nights < 0.90, ADR ≤ 1.15)
        if pace_ratio < 0.95 and nights_pace < 0.90 and adr_ratio <= 1.15:
            return 'LOW_BOOKING_PACE', self.DIAGNOSIS_RULES['low_booking_pace']['description'], 'moderate_discount', self.DIAGNOSIS_RULES['low_booking_pace']['action']
        
        # Rule 5: ADR Too Low (Pace < 0.95, Nights ≥ 0.90, ADR < 0.90)
        if pace_ratio < 0.95 and nights_pace >= 0.90 and adr_ratio < 0.90:
            return 'ADR_TOO_LOW', self.DIAGNOSIS_RULES['adr_too_low']['description'], 'raise_adr', self.DIAGNOSIS_RULES['adr_too_low']['action']
        
        # Rule 6: ADR Too High (Pace < 0.95, Nights ≥ 0.90, ADR > 1.15)
        if pace_ratio < 0.95 and nights_pace >= 0.90 and adr_ratio > 1.15:
            return 'ADR_TOO_HIGH', self.DIAGNOSIS_RULES['adr_too_high']['description'], 'reduce_adr', self.DIAGNOSIS_RULES['adr_too_high']['action']
        
        # Rule 7: Underperforming (Pace < 0.95, Nights ≥ 0.90, ADR 0.90-1.15)
        if pace_ratio < 0.95 and nights_pace >= 0.90 and 0.90 <= adr_ratio <= 1.15:
            return 'UNDERPERFORMING', self.DIAGNOSIS_RULES['underperforming']['description'], 'full_review', self.DIAGNOSIS_RULES['underperforming']['action']
        
        # Default fallback
        return 'REVIEW_NEEDED', 'Unable to match diagnosis rule - manual review needed', 'manual_review', 'Contact revenue manager for analysis'
    
    def _calculate_action_value(self, action_type, adr_ratio):
        """
        Calculate the potential impact of recommended action.
        
        Args:
            action_type: Type of action (raise_adr, reduce_adr, etc.)
            adr_ratio: Current ADR ratio
        
        Returns:
            Dictionary with action values and projections
        """
        current_adr = Decimal(str(self.evaluation_data['actual_adr']))
        expected_adr = Decimal(str(self.evaluation_data['expected_adr']))
        current_revenue_forecast = Decimal(str(self.evaluation_data['forecast_revenue']))
        potential_revenue = Decimal(str(self.evaluation_data['potential_revenue']))
        occupancy = Decimal(str(self.evaluation_data['expected_occupancy']))
        
        # Calculate new ADR based on action
        new_adr = current_adr
        adr_change_pct = 0
        
        if action_type == 'raise_adr':
            # Raise by 5-10% (use conservative 7.5%)
            adr_change_pct = 0.075
            new_adr = current_adr * Decimal('1.075')
        elif action_type == 'reduce_adr':
            # Reduce by 5-10% (use conservative 7.5%)
            adr_change_pct = -0.075
            new_adr = current_adr * Decimal('0.925')
        elif action_type == 'reduce_adr_aggressive':
            # Reduce by 10-15% (use conservative 12.5%)
            adr_change_pct = -0.125
            new_adr = current_adr * Decimal('0.875')
        elif action_type == 'moderate_discount':
            # Reduce by 5-10% (use conservative 7.5%)
            adr_change_pct = -0.075
            new_adr = current_adr * Decimal('0.925')
        
        # Calculate revenue impact
        # Assume occupancy improves slightly with lower prices (10% improvement on occupancy for price cuts)
        occupancy_multiplier = Decimal('1.10') if new_adr < current_adr else Decimal('1.0')
        potential_occupancy = min(occupancy * occupancy_multiplier, Decimal('1.0'))
        
        # Estimate impact on remaining days
        remaining_days = Decimal(str(self.evaluation_data['remaining_free_days']))
        rooms = Decimal(str(self.evaluation_data['rooms']))
        
        action_revenue_impact = remaining_days * rooms * potential_occupancy * new_adr
        new_forecast_revenue = current_revenue_forecast + action_revenue_impact
        
        return {
            'action_type': action_type,
            'current_adr': float(current_adr),
            'recommended_adr': float(new_adr),
            'adr_change_pct': adr_change_pct * 100,
            'current_forecast_revenue': float(current_revenue_forecast),
            'forecast_after_action': float(new_forecast_revenue),
            'revenue_impact': float(action_revenue_impact),
            'revenue_impact_pct': float((action_revenue_impact / current_revenue_forecast * 100)) if current_revenue_forecast > 0 else 0,
            'potential_occupancy_after_action': float(potential_occupancy),
            'occupancy_change': float((potential_occupancy - occupancy) * 100),
            'confidence': 'HIGH' if abs(adr_change_pct) <= 0.15 else 'MEDIUM',
        }
