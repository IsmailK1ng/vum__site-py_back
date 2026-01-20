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
    PromotionViewSet,
    BecomeADealerApplicationViewSet
)

router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')
router.register(r'contact', ContactFormViewSet, basename='contact')
router.register(r'job-applications', JobApplicationViewSet, basename='job-application')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'dealers', DealerViewSet, basename='dealers')
router.register(r'dealer-services', DealerServiceViewSet, basename='dealer-services')
router.register(r'become-dealer-page', BecomeADealerPageViewSet, basename='become-dealer-page')
router.register(r'dealer-applications', BecomeADealerApplicationViewSet, basename='dealer-applications')
router.register(r'promotions', PromotionViewSet, basename='promotions') 

urlpatterns = [
    path('', include(router.urls)),    
    path('uz/', include(router.urls)),
    path('ru/', include(router.urls)),
    path('en/', include(router.urls)),
]