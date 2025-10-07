from rest_framework.routers import DefaultRouter
from .views import NewsViewSet, ContactFormViewSet

router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')
router.register(r'contact', ContactFormViewSet, basename='contact')

urlpatterns = router.urls
