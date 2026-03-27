from django.contrib import admin
from django.db.models import Avg, Sum, Count
from .models import Property
from metrices.models import PropertyMetrics


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Admin configuration for Property model."""
    list_display = ['name', 'type', 'manager', 'total_revenue', 'average_occupancy', 'bookings_per_month', 'revenue_growth_rate', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'address', 'manager']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'type', 'manager')
        }),
        ('KPIs', {
            'fields': (
                'total_revenue',
                'average_occupancy',
                'bookings_per_month',
                'revenue_growth_rate',
            ),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = (
        'total_revenue',
        'average_occupancy', 
        'bookings_per_month',
        'revenue_growth_rate',
    )
    
    def total_revenue(self, obj):
        """Calculate total revenue for the property."""
        metrics = PropertyMetrics.objects.filter(property=obj)
        total = metrics.aggregate(total=Sum('revenue'))['total']
        return f"${total:,.2f}" if total else "$0.00"
    total_revenue.short_description = "Total Revenue"
    
    def average_occupancy(self, obj):
        """Calculate average occupancy for the property."""
        metrics = PropertyMetrics.objects.filter(property=obj)
        avg = metrics.aggregate(avg=Avg('occupancy'))['avg']
        return f"{avg:.1f}%" if avg else "0%"
    average_occupancy.short_description = "Average Occupancy"
    
    def bookings_per_month(self, obj):
        """Calculate average bookings per month."""
        metrics = PropertyMetrics.objects.filter(property=obj)
        agg = metrics.aggregate(
            total_bookings=Sum('bookings'),
            count=Count('id')
        )
        if agg['count'] and agg['total_bookings']:
            bookings_per_month = agg['total_bookings'] / agg['count']
            return f"{bookings_per_month:.1f}"
        return "0"
    bookings_per_month.short_description = "Bookings per Month"
    
    def revenue_growth_rate(self, obj):
        """Calculate revenue growth rate between first and latest month."""
        metrics = PropertyMetrics.objects.filter(property=obj).order_by('month')
        
        if metrics.count() < 2:
            return "N/A (need 2+ months)"
        
        first = metrics.first()
        latest = metrics.last()
        
        if first.revenue == 0:
            return "N/A (first month revenue is 0)"
        
        growth_rate = ((latest.revenue - first.revenue) / first.revenue) * 100
        return f"{growth_rate:+.1f}%"
    revenue_growth_rate.short_description = "Revenue Growth Rate"
