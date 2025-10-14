from rest_framework.routers import DefaultRouter
from .views import KGVehicleViewSet, KGFeedbackViewSet, KGHeroSlideViewSet

router = DefaultRouter()
router.register(r'vehicles', KGVehicleViewSet, basename='kg-vehicles')
router.register(r'feedback', KGFeedbackViewSet, basename='kg-feedback')
router.register(r'hero', KGHeroSlideViewSet, basename='kg-hero')  # НОВОЕ

urlpatterns = router.urls