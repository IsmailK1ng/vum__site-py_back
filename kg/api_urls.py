from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    KGVehicleViewSet, 
    KGFeedbackViewSet, 
    KGHeroSlideViewSet,
    KGFeedbackQuickUpdateViewSet,
    kg_stats_dashboard
)

router = DefaultRouter()
router.register(r'vehicles', KGVehicleViewSet, basename='kg-vehicles')
router.register(r'feedback', KGFeedbackViewSet, basename='kg-feedback')
router.register(r'hero', KGHeroSlideViewSet, basename='kg-hero')
router.register(r'feedback-update', KGFeedbackQuickUpdateViewSet, basename='kg-feedback-update')

urlpatterns = [
    path('stats/', kg_stats_dashboard, name='kg-stats'),
]

urlpatterns += router.urls