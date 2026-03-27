#!/usr/bin/env python
"""
Fix script for PropertyMetrics admin error.
Run this to identify and fix the corrupted database record.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propertyMetrics.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from metrices.models import PropertyMetrics
from properties.models import Property

def fix_issue():
    print("Checking PropertyMetrics record with pk=62...")
    
    try:
        pm = PropertyMetrics.objects.get(pk=62)
        print(f"  Property ID: {pm.property_id}")
        
        # Check if property exists
        prop_exists = Property.objects.filter(id=pm.property_id).exists()
        print(f"  Property exists: {prop_exists}")
        
        if not prop_exists:
            print("\n  ISSUE FOUND: Property record is missing (orphaned reference)")
            print("  Options:")
            print("    1. Delete the orphaned PropertyMetrics record")
            print("    2. Assign a valid property")
            
            choice = input("\nEnter choice (1 or 2): ").strip()
            
            if choice == '1':
                pm.delete()
                print("  Deleted orphaned PropertyMetrics record.")
            elif choice == '2':
                # Show available properties
                properties = Property.objects.all()
                print("\nAvailable Properties:")
                for p in properties:
                    print(f"  [{p.id}] {p.name}")
                
                prop_id = input("\nEnter property ID to assign: ").strip()
                try:
                    new_property = Property.objects.get(id=int(prop_id))
                    pm.property = new_property
                    pm.save()
                    print(f"  Assigned to property: {new_property.name}")
                except (Property.DoesNotExist, ValueError):
                    print("  Invalid property ID. No changes made.")
            else:
                print("  Invalid choice. No changes made.")
        else:
            print("\n  Property exists. Checking other potential issues...")
            print(f"  Property name: {pm.property.name}")
            
    except PropertyMetrics.DoesNotExist:
        print("  PropertyMetrics record with pk=62 does not exist!")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")

if __name__ == '__main__':
    fix_issue()