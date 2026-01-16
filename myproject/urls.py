from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.conf.urls.i18n import i18n_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from kg.views import kg_stats_dashboard
from main.views import set_language_get
from main.views_sitemap import sitemap_index, sitemap_uz, sitemap_ru, sitemap_en

admin.site.site_header = "FAW Admin"
admin.site.site_title = "FAW"
admin.site.index_title = "Админ панель VUM Site"

# ========== БАЗОВЫЕ РОУТЫ (без языка) ==========
urlpatterns = [
    path('robots.txt', serve, {'document_root': settings.BASE_DIR / 'main' / 'static', 'path': 'robots.txt'}),
    
    # ========== SITEMAP ==========
    path('sitemap.xml', sitemap_index, name='sitemap_index'),
    path('sitemap-uz.xml', sitemap_uz, name='sitemap_uz'),
    path('sitemap-ru.xml', sitemap_ru, name='sitemap_ru'),
    path('sitemap-en.xml', sitemap_en, name='sitemap_en'),
    
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

# ========== ОСНОВНЫЕ URL ТОЛЬКО ЧЕРЕЗ i18n_patterns ==========
urlpatterns += i18n_patterns(
    path('', include('main.urls')),  
    prefix_default_language=False  
)

# ========== МЕДИА И СТАТИКА (только DEBUG) ==========
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  