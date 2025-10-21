from rest_framework.routers import DefaultRouter
from .views import (
    KGVehicleViewSet, 
    KGFeedbackViewSet, 
    KGHeroSlideViewSet,
    KGFeedbackQuickUpdateViewSet  # ← ДОБАВИЛИ
)

router = DefaultRouter()
router.register(r'vehicles', KGVehicleViewSet, basename='kg-vehicles')
router.register(r'feedback', KGFeedbackViewSet, basename='kg-feedback')
router.register(r'hero', KGHeroSlideViewSet, basename='kg-hero')
router.register(r'feedback-update', KGFeedbackQuickUpdateViewSet, basename='kg-feedback-update')  # ← НОВОЕ

urlpatterns = router.urls