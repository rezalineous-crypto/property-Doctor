import logging
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from daily_metrics.serializers.property_report_upload_serializer import (
    PropertyReportUploadSerializer,
    DailyPropertyReportSerializer
)
from daily_metrics.services.property_report_import_service import (
    PropertyReportImportService
)
from daily_metrics.models import DailyPropertyReport

logger = logging.getLogger(__name__)


class PropertyReportUploadView(APIView):
    """
    API endpoint to upload and import daily property metrics from CSV/XLSX file.
    
    POST /api/daily-metrics/upload/
    
    Request:
        - file: CSV or XLSX file containing daily property metrics
        - data_type: Type of data ('actual' or 'otb')
        - dry_run: Optional boolean to validate without saving
    
    Response:
        - status: 'success', 'completed_with_errors', or 'failed'
        - created: Number of new records created
        - updated: Number of existing records updated
        - errors: List of error messages for failed rows
    """
    
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Handle the file upload and import request.
        """
        # Validate request data
        serializer = PropertyReportUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'status': 'failed',
                    'created': 0,
                    'updated': 0,
                    'errors': [
                        {'row': 0, 'error': f"{field}: {errors[0]}"}
                        for field, errors in serializer.errors.items()
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract validated data
        file = serializer.validated_data['file']
        data_type = serializer.validated_data.get('data_type', 'actual')
        dry_run = serializer.validated_data.get('dry_run', False)
        
        logger.info(
            f"Processing daily metrics upload: file={file.name}, "
            f"data_type={data_type}, dry_run={dry_run}, user={request.user}"
        )
        
        # Process the file using the import service
        import_service = PropertyReportImportService(
            data_type=data_type,
            dry_run=dry_run
        )
        
        result = import_service.process_file(file)
        
        # Determine appropriate HTTP status
        if result['status'] == 'failed':
            http_status = status.HTTP_400_BAD_REQUEST
        elif result['status'] == 'completed_with_errors':
            http_status = status.HTTP_207_MULTI_STATUS
        else:
            http_status = status.HTTP_200_OK
        
        # Add helpful message
        if result['status'] == 'success':
            result['message'] = (
                f"Successfully imported {result['created']} new, "
                f"updated {result['updated']} existing records"
            )
        elif result['status'] == 'completed_with_errors':
            result['message'] = (
                f"Imported {result['created']} new, "
                f"updated {result['updated']} existing records with "
                f"{len(result['errors'])} errors"
            )
        
        logger.info(
            f"Import completed: status={result['status']}, "
            f"created={result['created']}, updated={result['updated']}, "
            f"errors={len(result['errors'])}"
        )
        
        return Response(result, status=http_status)


class DailyPropertyReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DailyPropertyReport model with CRUD operations.
    
    list: GET - List all daily property reports with optional filtering
    create: POST - Create a new daily property report
    retrieve: GET - Retrieve a single daily property report
    update: PUT - Update an existing daily property report
    partial_update: PATCH - Partially update a daily property report
    destroy: DELETE - Delete a daily property report
    """
    
    queryset = DailyPropertyReport.objects.all()
    serializer_class = DailyPropertyReportSerializer
    
    # Filtering configuration
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    
    # Filter fields for exact matching
    filterset_fields = {
        'property': ['exact', 'in'],
        'date': ['exact', 'gte', 'lte'],
        'data_type': ['exact', 'in'],
    }
    
    # Search fields - searches property name
    search_fields = ['property__name']
    
    # Ordering fields
    ordering_fields = ['date', 'created_at', 'updated_at', 'property']
    ordering = ['-date']
    
    # Custom filtering for date range
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by property if provided
        property_id = self.request.query_params.get('property_id')
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        # Filter by start_date and end_date
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.select_related('property')