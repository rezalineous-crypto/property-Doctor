from rest_framework import serializers
from .models import PropertyMetrics


class PropertyMetricsSerializer(serializers.ModelSerializer):
    """Serializer for the PropertyMetrics model."""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = PropertyMetrics
        fields = [
            'id', 
            'property',
            'property_name',
            'month', 
            'revenue', 
            'occupancy', 
            'bookings', 
            'expenses',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_occupancy(self, value):
        """Validate that occupancy is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Occupancy must be between 0 and 100")
        return value
