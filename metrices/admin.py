from django.contrib import admin
from .models import PropertyMetrics


@admin.register(PropertyMetrics)
class PropertyMetricsAdmin(admin.ModelAdmin):
    """Admin configuration for PropertyMetrics model."""
    list_display = ['property', 'month', 'revenue', 'occupancy', 'bookings', 'expenses']
    list_filter = ['month', 'property']
    search_fields = ['property__name']
    ordering = ['-month']
    date_hierarchy = 'month'
