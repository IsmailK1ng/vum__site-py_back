from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from kg.views import kg_stats_dashboard  # 👈 импорт твоего дашборда

# Настройки админки
admin.site.site_header = "FAW Admin"
admin.site.site_title = "FAW"
admin.site.index_title = "Админ панель VUM Site"

urlpatterns = [
    # 👇 ВАЖНО: сначала ставим кастомный маршрут
    path('admin/kg/stats/', kg_stats_dashboard, name='kg-stats'),

    # Потом — встроенная админка
    path('admin/', admin.site.urls),

    path('i18n/', include('django.conf.urls.i18n')),
    path('nested_admin/', include('nested_admin.urls')),

    # HTML-страницы
    path('', include('main.urls')),

    # API эндпоинты
    path('api/', include('main.api_urls')),
    path('api/kg/', include('kg.api_urls')),

    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root='')
    