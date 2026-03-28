from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyConfigViewSet, property_evaluation_view, PropertyEvaluationTemplateView, property_diagnosis_view, PropertyDiagnosisTemplateView

router = DefaultRouter()
router.register(r'property-config', PropertyConfigViewSet, basename='property-config')

urlpatterns = [
    path('', include(router.urls)),
    path('property-evaluation/<int:property_id>/<str:month>/', property_evaluation_view, name='property-evaluation-api'),
    path('property-evaluation-view/<int:property_id>/<str:month>/', PropertyEvaluationTemplateView.as_view(), name='property-evaluation-html'),
    path('property-diagnosis/<int:property_id>/<str:month>/', property_diagnosis_view, name='property-diagnosis-api'),
    path('property-diagnosis-view/<int:property_id>/<str:month>/', PropertyDiagnosisTemplateView.as_view(), name='property-diagnosis-html'),
]
