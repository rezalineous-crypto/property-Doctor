from django.contrib import admin
from daily_metrics.models import DailyPropertyReport


@admin.register(DailyPropertyReport)
class DailyPropertyReportAdmin(admin.ModelAdmin):
    """Admin configuration for DailyPropertyReport model."""
    
    list_display = [
        'property', 'date', 'data_type', 'rooms', 'arrivals', 
        'departures', 'total_income', 'occupancy_percentage'
    ]
    list_filter = ['data_type', 'date', 'property']
    search_fields = ['property__name']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    fieldsets = (
        ('Property & Date', {
            'fields': ('property', 'date', 'data_type')
        }),
        ('Occupancy Metrics', {
            'fields': ('rooms', 'arrivals', 'departures', 'stay_over', 'bed_nights')
        }),
        ('Financial Metrics', {
            'fields': ('total_income', 'avg_room_rate', 'avg_guest_rate')
        }),
        ('Calculated Metrics', {
            'fields': ('occupancy_percentage', 'guest_per_room')
        }),
    )