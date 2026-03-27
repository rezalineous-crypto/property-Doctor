from django.db import models
from properties.models import Property


class DailyPropertyReport(models.Model):
    """
    Model representing daily performance metrics for a property.
    
    This model stores daily metrics data including occupancy, arrivals,
    departures, income, and other key performance indicators.
    """
    
    DATA_TYPE_CHOICES = [
        ('actual', 'Actual'),
        ('otb', 'On The Books'),
    ]
    
    property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='daily_reports'
    )
    date = models.DateField()
    data_type = models.CharField(
        max_length=10, 
        choices=DATA_TYPE_CHOICES, 
        default='actual'
    )
    
    # Occupancy metrics
    rooms = models.IntegerField(default=0)
    arrivals = models.IntegerField(default=0)
    departures = models.IntegerField(default=0)
    stay_over = models.IntegerField(default=0)
    bed_nights = models.IntegerField(default=0)
    
    # Financial metrics
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_room_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_guest_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Calculated metrics
    occupancy_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    guest_per_room = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', 'property', 'data_type']
        unique_together = ['property', 'date', 'data_type']
        indexes = [
            models.Index(fields=['date', 'data_type']),
            models.Index(fields=['property', 'date']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.date} ({self.data_type})"