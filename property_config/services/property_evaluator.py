from datetime import datetime
from decimal import Decimal
from calendar import monthrange
from django.db.models import Sum, Q
from property_config.models import PropertyConfig
from daily_metrics.models import DailyPropertyReport


class PropertyEvaluationService:
    """Service to evaluate property performance for a given month."""
    
    def __init__(self, property_obj, month, config, actual_data, otb_data, current_day, days_in_month, rooms):
        """Initialize service with property data and metrics."""
        self.property = property_obj
        self.month = month  # Format: YYYY-MM
        self.config = config
        self.actual_data = actual_data
        self.otb_data = otb_data
        self.current_day = current_day
        self.days_in_month = days_in_month
        self.rooms = rooms or 1
    
    @classmethod
    def for_property_month(cls, property_obj, month):
        """
        Factory method to create service for a property and month.
        
        Args:
            property_obj: Property instance
            month: String in format "YYYY-MM"
        
        Returns:
            PropertyEvaluationService instance
        """
        # Get PropertyConfig
        config = PropertyConfig.objects.filter(property=property_obj, month=month).first()
        if not config:
            raise ValueError(f"No PropertyConfig found for property {property_obj.id} and month {month}")
        
        # Parse month
        year, month_num = map(int, month.split('-'))
        days_in_month = monthrange(year, month_num)[1]
        
        # Get current day
        today = datetime.now().date()
        current_day = min(today.day, days_in_month)
        
        # Filter date range for the month
        month_start = f"{year}-{month_num:02d}-01"
        
        # Aggregate actual data (past)
        actual_data = DailyPropertyReport.objects.filter(
            property=property_obj,
            date__year=year,
            date__month=month_num,
            data_type='actual'
        ).aggregate(
            total_nights=Sum('bed_nights'),
            total_revenue=Sum('total_income')
        )
        
        # Aggregate OTB data (future bookings)
        otb_data = DailyPropertyReport.objects.filter(
            property=property_obj,
            date__year=year,
            date__month=month_num,
            data_type='otb'
        ).aggregate(
            total_nights=Sum('bed_nights'),
            total_revenue=Sum('total_income')
        )
        
        # Get rooms from property (use 1 as fallback)
        rooms = getattr(property_obj, 'number_of_rooms', 1) or 1
        
        return cls(
            property_obj=property_obj,
            month=month,
            config=config,
            actual_data=actual_data,
            otb_data=otb_data,
            current_day=current_day,
            days_in_month=days_in_month,
            rooms=rooms
        )
    
    def evaluate(self):
        """Calculate all metrics and return results dictionary."""
        # Extract aggregated data
        actual_nights_td = self.actual_data.get('total_nights') or 0
        actual_revenue_td = Decimal(str(self.actual_data.get('total_revenue') or 0))
        
        otb_nights = self.otb_data.get('total_nights') or 0
        otb_revenue = Decimal(str(self.otb_data.get('total_revenue') or 0))
        
        # Calculate Expected Metrics
        expected_metrics = self._calculate_expected_metrics()
        
        # Calculate KPIs
        kpis = self._calculate_kpis(
            actual_nights_td,
            actual_revenue_td,
            expected_metrics
        )
        
        # Calculate Forecast & Potential
        forecast = self._calculate_forecast(
            actual_revenue_td,
            otb_revenue,
            otb_nights,
            expected_metrics
        )
        
        # Validation Flags
        validation = self._calculate_validation()
        
        return {
            # Input Data
            'property_id': self.property.id,
            'property_name': self.property.name,
            'month': self.month,
            'current_day': self.current_day,
            'days_in_month': self.days_in_month,
            'rooms': self.rooms,
            
            # Actual Data
            'actual_nights_td': float(actual_nights_td),
            'actual_revenue_td': float(actual_revenue_td),
            'actual_adr_td': float(actual_revenue_td / actual_nights_td) if actual_nights_td > 0 else 0,
            
            # OTB Data
            'otb_nights': float(otb_nights),
            'otb_revenue': float(otb_revenue),
            
            # Expected Metrics
            **expected_metrics,
            
            # KPIs
            **kpis,
            
            # Forecast & Potential
            **forecast,
            
            # Validation
            **validation,
        }
    
    def _calculate_expected_metrics(self):
        """Calculate expected metrics based on market data and PAF."""
        market_adr = Decimal(str(self.config.market_adr))
        market_occupancy = Decimal(str(self.config.market_occupancy))
        paf = Decimal(str(self.config.paf))
        
        # Expected ADR
        expected_adr = market_adr * paf
        
        # Expected Occupancy
        expected_occupancy = market_occupancy
        
        # Expected Nights (full month)
        expected_nights_month = Decimal(str(self.days_in_month)) * Decimal(str(self.rooms)) * expected_occupancy
        
        # Expected Revenue (full month)
        expected_revenue_month = expected_nights_month * expected_adr
        
        # Expected Nights to Date
        expected_nights_td = Decimal(str(self.current_day)) * Decimal(str(self.rooms)) * expected_occupancy
        
        # Expected Revenue to Date
        expected_revenue_td = expected_nights_td * expected_adr
        
        return {
            'expected_adr': float(expected_adr),
            'expected_occupancy': float(expected_occupancy),
            'expected_nights_month': float(expected_nights_month),
            'expected_revenue_month': float(expected_revenue_month),
            'expected_nights_td': float(expected_nights_td),
            'expected_revenue_td': float(expected_revenue_td),
        }
    
    def _calculate_kpis(self, actual_nights_td, actual_revenue_td, expected_metrics):
        """Calculate KPIs comparing actual vs expected."""
        expected_revenue_td = Decimal(str(expected_metrics['expected_revenue_td']))
        expected_nights_td = Decimal(str(expected_metrics['expected_nights_td']))
        expected_adr = Decimal(str(expected_metrics['expected_adr']))
        
        # Pace Ratio (Revenue)
        pace_ratio = (actual_revenue_td / expected_revenue_td) if expected_revenue_td > 0 else 0
        
        # Nights Pace Ratio
        nights_pace_ratio = (Decimal(str(actual_nights_td)) / expected_nights_td) if expected_nights_td > 0 else 0
        
        # Actual ADR
        actual_adr = (actual_revenue_td / Decimal(str(actual_nights_td))) if actual_nights_td > 0 else 0
        
        # ADR Ratio
        adr_ratio = (actual_adr / expected_adr) if expected_adr > 0 else 0
        
        # ADR Gap
        adr_gap = actual_adr - expected_adr
        
        return {
            'pace_ratio': float(pace_ratio),
            'pace_ratio_vs_threshold': float(pace_ratio) >= float(self.config.pace_threshold),
            'nights_pace_ratio': float(nights_pace_ratio),
            'nights_pace_vs_low': float(nights_pace_ratio) >= float(self.config.nights_low_threshold),
            'nights_pace_vs_high': float(nights_pace_ratio) <= float(self.config.nights_high_threshold),
            'adr_ratio': float(adr_ratio),
            'adr_gap': float(adr_gap),
            'adr_vs_low': float(adr_ratio) >= float(self.config.adr_low_threshold),
            'adr_vs_high': float(adr_ratio) <= float(self.config.adr_high_threshold),
            'actual_adr': float(actual_adr),
        }
    
    def _calculate_forecast(self, actual_revenue_td, otb_revenue, otb_nights, expected_metrics):
        """Calculate forecast and potential revenue."""
        expected_adr = Decimal(str(expected_metrics['expected_adr']))
        expected_occupancy = Decimal(str(expected_metrics['expected_occupancy']))
        expected_revenue_month = Decimal(str(expected_metrics['expected_revenue_month']))
        
        # Forecast Revenue
        forecast_revenue = actual_revenue_td + otb_revenue
        
        # Remaining Free Days
        remaining_days = self.days_in_month - self.current_day - otb_nights
        remaining_days = max(Decimal('0'), Decimal(str(remaining_days)))
        
        # Potential Revenue from remaining days
        potential_revenue_remaining = remaining_days * Decimal(str(self.rooms)) * expected_occupancy * expected_adr
        
        # Total Potential Revenue
        potential_revenue = forecast_revenue + potential_revenue_remaining
        
        # Forecast vs Target
        forecast_vs_target = forecast_revenue - expected_revenue_month
        
        # Forecast vs Target %
        forecast_vs_target_pct = (forecast_vs_target / expected_revenue_month * 100) if expected_revenue_month > 0 else 0
        
        return {
            'forecast_revenue': float(forecast_revenue),
            'potential_revenue': float(potential_revenue),
            'remaining_free_days': float(remaining_days),
            'forecast_vs_target': float(forecast_vs_target),
            'forecast_vs_target_pct': float(forecast_vs_target_pct),
        }
    
    def _calculate_validation(self):
        """Calculate data validation flags."""
        has_revenue = self.actual_data.get('total_revenue', 0) is not None and self.actual_data.get('total_revenue', 0) > 0
        has_nights = self.actual_data.get('total_nights', 0) is not None and self.actual_data.get('total_nights', 0) > 0
        data_valid = has_revenue and has_nights
        
        return {
            'has_revenue_data': has_revenue,
            'has_nights_data': has_nights,
            'data_valid': data_valid,
        }
