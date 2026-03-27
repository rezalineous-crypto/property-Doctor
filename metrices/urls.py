from django.urls import path
from .views import PropertyMetricsImportView

urlpatterns = [
    path('import/', PropertyMetricsImportView.as_view(), name='propertymetrics-import'),
]
