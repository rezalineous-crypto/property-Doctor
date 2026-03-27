from rest_framework import serializers
from .models import Property


class PropertySerializer(serializers.ModelSerializer):
    """Serializer for the Property model."""
    
    class Meta:
        model = Property
        fields = [
            'id', 
            'name', 
            'address', 
            'type', 
            'manager',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
