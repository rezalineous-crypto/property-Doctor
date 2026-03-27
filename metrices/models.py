from django.db import models
from properties.models import Property


class PropertyMetrics(models.Model):
    """Model representing performance metrics for a property."""
    
    property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='metrics'
    )
    month = models.DateField()  # First day of the month
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    occupancy = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    bookings = models.PositiveIntegerField(default=0)
    expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month']
        unique_together = ['property', 'month']
    
    def __str__(self):
        return f"{self.property.name} - {self.month.strftime('%Y-%m')}"
