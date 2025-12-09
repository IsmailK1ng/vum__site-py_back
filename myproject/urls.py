# myproject/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from kg.views import kg_stats_dashboard
from main.views import set_language_get

admin.site.site_header = "FAW Admin"
admin.site.site_title = "FAW"
admin.site.index_title = "Админ панель VUM Site"

# ========== БАЗОВЫЕ РОУТЫ (без языка) ==========
urlpatterns = [
    path('admin/kg/stats/', kg_stats_dashboard, name='kg-stats'),
    path('admin/', admin.site.urls),
    path('set-language/', set_language_get, name='set_language'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('nested_admin/', include('nested_admin.urls')),
    
    # API endpoints
    path('api/kg/', include('kg.api_urls')),
    path('api/', include('main.api_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

urlpatterns += [
    path('', include('main.urls')), 
]

urlpatterns += i18n_patterns(
    path('', include('main.urls')),
    prefix_default_language=False  
)

# ========== МЕДИА И СТАТИКА (только DEBUG) ==========
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root='')