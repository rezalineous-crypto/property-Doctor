from django.db import models


class Property(models.Model):
    """Model representing a property in the system."""
    
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('condo', 'Condo'),
        ('townhouse', 'Townhouse'),
        ('commercial', 'Commercial'),
    ]
    
    UNIT_CHOICES = [
        ('studio', 'Studio'),
        ('1B', '1 Bedroom'),
        ('2B', '2 Bedroom'),
        ('3B', '3 Bedroom'),
        ('4B', '4 Bedroom'),
        ('5B', '5 Bedroom'),
    ]
    
    name = models.CharField(max_length=200)
    address = models.TextField()
    type = models.CharField(max_length=50, choices=PROPERTY_TYPES)
    manager = models.CharField(max_length=200)
    
    # Additional fields for daily metrics
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, blank=True, null=True)
    number_of_rooms = models.IntegerField(default=1)
    room_type = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
