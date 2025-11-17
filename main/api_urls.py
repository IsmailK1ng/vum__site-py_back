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

# Создаём роутеры для каждого языка
uz_router = DefaultRouter()
uz_router.register(r'news', NewsViewSet, basename='news-uz')
uz_router.register(r'contact', ContactFormViewSet, basename='contact-uz')
uz_router.register(r'job-applications', JobApplicationViewSet, basename='job-application-uz')
uz_router.register(r'products', ProductViewSet, basename='products-uz')
uz_router.register(r'dealers', DealerViewSet, basename='dealers-uz')
uz_router.register(r'dealer-services', DealerServiceViewSet, basename='dealer-services-uz')
uz_router.register(r'become-dealer-page', BecomeADealerPageViewSet, basename='become-dealer-page-uz')
uz_router.register(r'dealer-applications', BecomeADealerApplicationViewSet, basename='dealer-applications-uz')

# Роутер для RU
ru_router = DefaultRouter()
ru_router.register(r'news', NewsViewSet, basename='news-ru')
ru_router.register(r'contact', ContactFormViewSet, basename='contact-ru')
ru_router.register(r'job-applications', JobApplicationViewSet, basename='job-application-ru')
ru_router.register(r'products', ProductViewSet, basename='products-ru')
ru_router.register(r'dealers', DealerViewSet, basename='dealers-ru')
ru_router.register(r'dealer-services', DealerServiceViewSet, basename='dealer-services-ru')
ru_router.register(r'become-dealer-page', BecomeADealerPageViewSet, basename='become-dealer-page-ru')
ru_router.register(r'dealer-applications', BecomeADealerApplicationViewSet, basename='dealer-applications-ru')

# Роутер для EN
en_router = DefaultRouter()
en_router.register(r'news', NewsViewSet, basename='news-en')
en_router.register(r'contact', ContactFormViewSet, basename='contact-en')
en_router.register(r'job-applications', JobApplicationViewSet, basename='job-application-en')
en_router.register(r'products', ProductViewSet, basename='products-en')
en_router.register(r'dealers', DealerViewSet, basename='dealers-en')
en_router.register(r'dealer-services', DealerServiceViewSet, basename='dealer-services-en')
en_router.register(r'become-dealer-page', BecomeADealerPageViewSet, basename='become-dealer-page-en')
en_router.register(r'dealer-applications', BecomeADealerApplicationViewSet, basename='dealer-applications-en')

urlpatterns = [
    path('uz/', include(uz_router.urls)),
    path('ru/', include(ru_router.urls)),
    path('en/', include(en_router.urls)),
]