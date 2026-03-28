from django.contrib import admin
from .models import PropertyConfig


@admin.register(PropertyConfig)
class PropertyConfigAdmin(admin.ModelAdmin):
    list_display = ['property', 'month', 'market_adr', 'market_occupancy', 'paf', 'created_at']
    list_filter = ['month', 'property', 'created_at']
    search_fields = ['property__name', 'month']
    ordering = ['-month', 'property']

