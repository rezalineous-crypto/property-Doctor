import csv
import io
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from django.db import transaction
from .models import Property
from .serializers import PropertySerializer


class PropertyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property model with CRUD operations.
    
    list: GET - List all properties with optional filtering by name or manager
    create: POST - Create a new property
    retrieve: GET - Retrieve a single property
    update: PUT - Update an existing property
    partial_update: PATCH - Partially update a property
    destroy: DELETE - Delete a property
    """
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    
    # Filtering configuration
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    
    # Filter fields for exact matching
    filterset_fields = {
        'type': ['exact', 'in'],
        'manager': ['exact', 'contains'],
    }
    
    # Search fields - searches name and manager
    search_fields = ['name', 'manager', 'address']
    
    # Ordering fields
    ordering_fields = ['name', 'created_at', 'updated_at', 'type', 'manager']
    ordering = ['name']


class PropertyImportView(APIView):
    """
    API endpoint to import Properties from CSV file.
    
    Expected CSV columns:
    - name: Property name (required, unique)
    - address: Property address (required)
    - type: Property type - apartment, house, condo, townhouse, commercial (required)
    - manager: Manager name (required)
    """
    parser_classes = [MultiPartParser]
    
    def post(self, request):
        # Try to get file from different sources
        csv_file = None
        
        # Check request.FILES
        if request.FILES:
            csv_file = request.FILES.get('file')
        # Check request.data (for form-data or JSON with base64)
        elif hasattr(request, 'data') and request.data:
            csv_file = request.data.get('file')
        
        if not csv_file:
            # Debug: show what's available
            return Response(
                {
                    'error': 'No file provided',
                    'debug': {
                        'FILES_keys': list(request.FILES.keys()) if request.FILES else [],
                        'data_keys': list(request.data.keys()) if hasattr(request, 'data') and request.data else []
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        if not csv_file.name.endswith('.csv'):
            return Response(
                {'error': 'File must be a CSV file'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decode and parse CSV
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            
            # Validate required columns
            required_columns = ['name', 'address', 'type', 'manager']
            if not all(col in csv_reader.fieldnames for col in required_columns):
                return Response(
                    {'error': f'CSV must contain columns: {required_columns}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Valid property types
            valid_types = ['apartment', 'house', 'condo', 'townhouse', 'commercial']
            
            # Process rows
            results = {
                'created': 0,
                'updated': 0,
                'errors': []
            }
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):  # start=2 accounts for header
                    try:
                        name = row['name'].strip()
                        address = row['address'].strip()
                        prop_type = row['type'].strip().lower()
                        manager = row['manager'].strip()
                        
                        # Validate required fields
                        if not name:
                            results['errors'].append({
                                'row': row_num,
                                'error': 'Name is required'
                            })
                            continue
                        
                        if not address:
                            results['errors'].append({
                                'row': row_num,
                                'error': 'Address is required'
                            })
                            continue
                        
                        if not manager:
                            results['errors'].append({
                                'row': row_num,
                                'error': 'Manager is required'
                            })
                            continue
                        
                        # Validate property type
                        if prop_type not in valid_types:
                            results['errors'].append({
                                'row': row_num,
                                'error': f"Invalid type '{prop_type}'. Must be one of: {', '.join(valid_types)}"
                            })
                            continue
                        
                        # Create or update property
                        property_obj, created = Property.objects.update_or_create(
                            name=name,
                            defaults={
                                'address': address,
                                'type': prop_type,
                                'manager': manager,
                            }
                        )
                        
                        if created:
                            results['created'] += 1
                        else:
                            results['updated'] += 1
                            
                    except Exception as e:
                        results['errors'].append({
                            'row': row_num,
                            'error': str(e)
                        })
            
            # Return success response
            if results['errors']:
                return Response({
                    'status': 'completed_with_errors',
                    'message': f"Imported {results['created']} new, updated {results['updated']} existing records",
                    'results': results
                }, status=status.HTTP_207_MULTI_STATUS)
            
            return Response({
                'status': 'success',
                'message': f"Successfully imported {results['created']} new, updated {results['updated']} existing records",
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to process CSV: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
