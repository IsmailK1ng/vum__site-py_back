from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NewsViewSet, 
    ContactFormViewSet, 
    JobApplicationViewSet,
    ProductViewSet  # ← ДОБАВИЛИ
)

# Роутер для UZ
uz_router = DefaultRouter()
uz_router.register(r'news', NewsViewSet, basename='news')
uz_router.register(r'contact', ContactFormViewSet, basename='contact')
uz_router.register(r'job-applications', JobApplicationViewSet, basename='job-application')
uz_router.register(r'products', ProductViewSet, basename='products')  # ← ДОБАВИЛИ

urlpatterns = [
    # API для faw.uz
    path('uz/', include(uz_router.urls)),
    
    # API для faw.kg
    path('kg/', include('kg.urls')),
]

## 🚀 Как использовать API

### 1️⃣ Список всех машин:
### GET http://localhost:8000/api/uz/products/

### 2️⃣ Только самосвалы:
### GET http://localhost:8000/api/uz/products/?category=dump_truck

### 3️⃣ Только тягачи:
### GET http://localhost:8000/api/uz/products/?category=tractor

### 4️⃣ Детальная страница по slug:
### GET http://localhost:8000/api/uz/products/faw-tiger-v-4x2/

### 5️⃣ Детальная страница по ID:
### GET http://localhost:8000/api/uz/products/1/