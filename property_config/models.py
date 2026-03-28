from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from properties.models import Property


class PropertyConfig(models.Model):
    """Monthly configuration for a property used in analytics and decision-making."""
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    month = models.CharField(
        max_length=7,
        validators=[RegexValidator(r'^\d{4}-\d{2}$', 'Format must be YYYY-MM')]
    )

    # Market Inputs (user-provided)
    market_adr = models.DecimalField(max_digits=10, decimal_places=2)
    market_occupancy = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    # Adjustment
    paf = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.0'))

    # Thresholds (with defaults)
    pace_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.95,
        validators=[MinValueValidator(0.0)]
    )
    nights_low_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.90,
        validators=[MinValueValidator(0.0)]
    )
    nights_high_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.05,
        validators=[MinValueValidator(0.0)]
    )
    adr_low_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.90,
        validators=[MinValueValidator(0.0)]
    )
    adr_high_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.15,
        validators=[MinValueValidator(0.0)]
    )
    early_month_guard_days = models.IntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("property", "month")
        indexes = [
            models.Index(fields=['property', 'month']),
            models.Index(fields=['month']),
        ]

    def __str__(self):
        return f"{self.property.name} - {self.month}"

