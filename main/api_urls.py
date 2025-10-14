from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsViewSet, ContactFormViewSet

# Роутер для UZ
uz_router = DefaultRouter()
uz_router.register(r'news', NewsViewSet, basename='news')
uz_router.register(r'contact', ContactFormViewSet, basename='contact')

urlpatterns = [
    # API для faw.uz
    path('uz/', include(uz_router.urls)),
    
    # API для faw.kg
    path('kg/', include('kg.urls')),  # ← ИСПРАВЛЕНО
]