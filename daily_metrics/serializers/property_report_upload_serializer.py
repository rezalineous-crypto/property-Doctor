from rest_framework import serializers
from django.utils import timezone

from daily_metrics.models import DailyPropertyReport


class PropertyReportUploadSerializer(serializers.Serializer):
    """
    Serializer for validating the daily property metrics upload request.
    
    This serializer handles input validation for the file upload endpoint,
    ensuring the file is present and has the correct extension, and that
    the data_type is valid.
    """
    
    FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB limit
    
    DATA_TYPE_CHOICES = [
        ('actual', 'Actual'),
        ('otb', 'On The Books'),
    ]
    
    VALID_EXTENSIONS = ['.csv', '.xlsx', '.xls']
    
    file = serializers.FileField(
        required=True,
        help_text="CSV or XLSX file containing daily property metrics"
    )
    data_type = serializers.ChoiceField(
        choices=DATA_TYPE_CHOICES,
        default='actual',
        help_text="Type of data: 'actual' or 'otb' (On The Books)"
    )
    dry_run = serializers.BooleanField(
        required=False,
        default=False,
        help_text="If true, validates data without saving to database"
    )
    
    def validate_file(self, value):
        """
        Validate that the uploaded file is a valid CSV or XLSX file.
        """
        # Check file extension
        file_name = value.name.lower()
        has_valid_extension = any(file_name.endswith(ext) for ext in self.VALID_EXTENSIONS)
        
        if not has_valid_extension:
            raise serializers.ValidationError(
                f"File must be one of: {', '.join(self.VALID_EXTENSIONS)}"
            )
        
        # Check file size
        if value.size > self.FILE_MAX_SIZE:
            raise serializers.ValidationError(
                f"File size must be less than {self.FILE_MAX_SIZE / (1024 * 1024)} MB"
            )
        
        return value
    
    def validate_data_type(self, value):
        """
        Ensure data_type is lowercase for consistency.
        """
        return value.lower()


class DailyPropertyReportSerializer(serializers.ModelSerializer):
    """
    Serializer for DailyPropertyReport model.
    """
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = DailyPropertyReport
        fields = [
            'id', 'property', 'property_name', 'date', 'data_type',
            'rooms', 'arrivals', 'departures', 'stay_over',
            'total_income', 'avg_room_rate', 'bed_nights',
            'avg_guest_rate', 'occupancy_percentage', 'guest_per_room',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DailyPropertyReportImportSerializer(serializers.Serializer):
    """
    Serializer for individual daily property report records during import.
    Used for validation during import process.
    """
    
    # Required fields
    date = serializers.DateField(required=True)
    hotel = serializers.CharField(max_length=200, required=True)
    rooms = serializers.IntegerField(min_value=0, required=True)
    arrivals = serializers.IntegerField(min_value=0, required=True)
    departures = serializers.IntegerField(min_value=0, required=True)
    stay_over = serializers.IntegerField(min_value=0, required=True)
    total_income = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=0, 
        required=True
    )
    average_room_rate = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=0, 
        required=True
    )
    bed_nights = serializers.IntegerField(min_value=0, required=True)
    average_guest_rate = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=0, 
        required=True
    )
    occupancy_percentage = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=0, 
        max_value=100, 
        required=True
    )
    guest_per_room = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=0, 
        required=True
    )
    
    # Optional fields
    unit = serializers.CharField(max_length=20, required=False, allow_null=True)
    room_type = serializers.CharField(max_length=100, required=False, allow_null=True)
    
    def validate_occupancy_percentage(self, value):
        """Validate occupancy percentage is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Occupancy percentage must be between 0 and 100"
            )
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Ensure non-negative integers
        numeric_fields = [
            'rooms', 'arrivals', 'departures', 'stay_over', 'bed_nights'
        ]
        
        for field in numeric_fields:
            if field in attrs and attrs[field] < 0:
                raise serializers.ValidationError({
                    field: f"{field} must be non-negative"
                })
        
        return attrs