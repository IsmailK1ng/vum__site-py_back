# myproject/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language as django_set_language
from django.utils import translation
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from kg.views import kg_stats_dashboard
from main.views_sitemap import sitemap_index, sitemap_uz, sitemap_ru, sitemap_en

admin.site.site_header = "FAW Admin"
admin.site.site_title = "FAW"
admin.site.index_title = "Админ панель VUM Site"


def set_language(request):
    """Обёртка над django.views.i18n.set_language.

    Проблема Django: при i18n_patterns(prefix_default_language=False) LocaleMiddleware
    для URL без префикса (например /set-language/) форсит дефолтный язык, игнорируя cookie.
    Из-за этого translate_url() внутри set_language вызывается в UZ-контексте и не может
    разрезолвить URL вроде /ru/about/ → редирект возвращается без перевода.

    Решение: перед вызовом стандартного view принудительно активируем язык на основе
    next_url (если он начинается с /ru/ или /en/), чтобы translate_url отработал.
    """
    if request.method == 'POST':
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '/')
        supported = {code for code, _ in settings.LANGUAGES}
        # Определяем язык next_url по префиксу
        parts = next_url.lstrip('/').split('/', 1)
        if parts and parts[0] in supported:
            translation.activate(parts[0])
    return django_set_language(request)

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
    # Встроенный Django view: меняет язык, ставит cookie, корректно переписывает URL
    # на новый языковой префикс (через translate_url) и редиректит на 'next'.
    path('set-language/', set_language, name='set_language'),
    path('nested_admin/', include('nested_admin.urls')),

    # ========== API БЕЗ ЯЗЫКА ==========
    path('api/kg/', include('kg.api_urls')),
    path('api/', include('main.api_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Все страницы сайта — через i18n_patterns.
# Для языка по умолчанию (uz) префикс отсутствует благодаря prefix_default_language=False.
# Для остальных языков URL-префикс добавляется автоматически: /ru/about/, /en/about/.
urlpatterns += i18n_patterns(
    path('', include('main.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)