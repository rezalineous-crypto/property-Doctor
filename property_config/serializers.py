from rest_framework import serializers
from .models import PropertyConfig


class PropertyConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyConfig
        fields = "__all__"
