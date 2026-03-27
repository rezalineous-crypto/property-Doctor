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
    
    name = models.CharField(max_length=200)
    address = models.TextField()
    type = models.CharField(max_length=50, choices=PROPERTY_TYPES)
    manager = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
