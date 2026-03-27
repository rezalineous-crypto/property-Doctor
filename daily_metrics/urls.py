from django.urls import path, include
from rest_framework.routers import DefaultRouter

from daily_metrics.views.property_report_upload_view import (
    PropertyReportUploadView,
    DailyPropertyReportViewSet
)

# Create router for ViewSet
router = DefaultRouter()
router.register(r'reports', DailyPropertyReportViewSet, basename='daily-property-report')

urlpatterns = [
    # Upload endpoint
    path('upload/', PropertyReportUploadView.as_view(), name='daily-metrics-upload'),
    
    # Include router URLs
    path('', include(router.urls)),
]