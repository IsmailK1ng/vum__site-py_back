from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NewsViewSet, 
    ContactFormViewSet, 
    JobApplicationViewSet,
    ProductViewSet,
    DealerViewSet,
    DealerServiceViewSet,
    BecomeADealerPageViewSet,
    BecomeADealerApplicationViewSet
)

# Роутер для UZ
uz_router = DefaultRouter()
uz_router.register(r'news', NewsViewSet, basename='news')
uz_router.register(r'contact', ContactFormViewSet, basename='contact')
uz_router.register(r'job-applications', JobApplicationViewSet, basename='job-application')
uz_router.register(r'products', ProductViewSet, basename='products')
uz_router.register(r'dealers', DealerViewSet, basename='dealers')
uz_router.register(r'dealer-services', DealerServiceViewSet, basename='dealer-services')
uz_router.register(r'become-dealer-page', BecomeADealerPageViewSet, basename='become-dealer-page')
uz_router.register(r'dealer-applications', BecomeADealerApplicationViewSet, basename='dealer-applications')

urlpatterns = [
    path('uz/', include(uz_router.urls)),
    path('kg/', include('kg.api_urls')),
]