# main/kg_api_urls.py
from rest_framework.routers import DefaultRouter
from .kg_views import KGVehicleViewSet, KGFeedbackViewSet, FeatureIconViewSet

router = DefaultRouter()
router.register(r'vehicles', KGVehicleViewSet, basename='kg-vehicles')
router.register(r'feedback', KGFeedbackViewSet, basename='kg-feedback')
router.register(r'features', FeatureIconViewSet, basename='kg-features')

urlpatterns = router.urls