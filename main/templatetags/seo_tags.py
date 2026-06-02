# main/templatetags/seo_tags.py

from urllib.parse import urlencode, parse_qsl
from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django.utils import translation
from django.conf import settings

register = template.Library()

# Tracking-параметры которые вырезаются из canonical/hreflang.
# Они не идентифицируют контент — это маркетинговый шум, создающий дубли в Google.
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'fbclid', 'gclid', 'yclid', 'msclkid',
    'ym_uid', 'ym_counter',
    '_ga', '_gl',
}


def _clean_query_string(query_string):
    """Возвращает query-строку без tracking-параметров. Контентные параметры (category и пр.) сохраняются."""
    if not query_string:
        return ''
    kept = [(k, v) for k, v in parse_qsl(query_string, keep_blank_values=True)
            if k not in TRACKING_PARAMS]
    return urlencode(kept) if kept else ''


def _canonical_base(request):
    """Возвращает протокол+хост для canonical/hreflang.

    DEBUG  → request.get_host() (удобно для локалки).
    Прод  → жёстко зашитый https://faw.uz (не зависит от Host-заголовка).
    """
    if settings.DEBUG:
        return f"{request.scheme}://{request.get_host()}"
    return "https://faw.uz"


@register.filter(name='with_lang_prefix')
def with_lang_prefix(url, lang_code=None):
    """Добавляет языковой префикс к URL, если язык не дефолтный.

    Используется для ссылок которые хранятся в БД (NavItem.url, SocialLink.url и т.д.)
    в "нейтральном" виде (например '/about/'). Шаблон сам подмешивает язык:
        <a href="{{ item.url|with_lang_prefix:LANGUAGE_CODE }}">

    Правила:
      - Внешние ссылки (http://, https://, //, mailto:, tel:) — возвращаются как есть.
      - Якоря (#anchor) — как есть.
      - Если язык дефолтный (LANGUAGE_CODE из settings, обычно 'uz') — префикс не добавляется.
      - Если в URL уже есть префикс /ru/ или /en/ — повторно не добавляется.
      - Для UZ-страниц лишний префикс /uz/ снимается.
    """
    if not url:
        return url

    default_lang = settings.LANGUAGE_CODE.split('-')[0]
    lang = (lang_code or default_lang).split('-')[0]
    supported = {code for code, _ in settings.LANGUAGES}

    # Внешние ссылки и якоря не трогаем
    if url.startswith(('http://', 'https://', '//', 'mailto:', 'tel:', '#', 'javascript:')):
        return url

    # Снимаем существующий префикс если есть (для повторной сборки под нужный язык)
    parts = url.lstrip('/').split('/', 1)
    if parts and parts[0] in supported:
        rest = parts[1] if len(parts) > 1 else ''
        url = '/' + rest if rest else '/'

    # Нормализуем начальный слеш
    if not url.startswith('/'):
        url = '/' + url

    # Для дефолтного языка префикс не добавляем
    if lang == default_lang or lang not in supported:
        return url

    # Добавляем префикс
    return f'/{lang}{url}'


@register.simple_tag(takes_context=True)
def hreflang_tags(context):
    """Генерирует hreflang теги для текущей страницы.

    Контентные query-параметры (category и пр.) сохраняются, tracking (utm_*, fbclid и т.д.) удаляются.
    """
    request = context.get('request')
    if not request:
        return ''

    url_name = request.resolver_match.url_name if request.resolver_match else None
    if not url_name:
        return ''

    domain = _canonical_base(request)
    url_kwargs = request.resolver_match.kwargs if request.resolver_match else {}

    clean_qs = _clean_query_string(request.META.get('QUERY_STRING', ''))
    query_suffix = f'?{clean_qs}' if clean_qs else ''

    current_language = translation.get_language()
    tags = []

    try:
        translation.activate('uz')
        uz_url = reverse(url_name, kwargs=url_kwargs)
        tags.append(f'<link rel="alternate" hreflang="uz" href="{domain}{uz_url}{query_suffix}" />')
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{domain}{uz_url}{query_suffix}" />')

        translation.activate('ru')
        ru_url = reverse(url_name, kwargs=url_kwargs)
        tags.append(f'<link rel="alternate" hreflang="ru" href="{domain}{ru_url}{query_suffix}" />')

        translation.activate('en')
        en_url = reverse(url_name, kwargs=url_kwargs)
        tags.append(f'<link rel="alternate" hreflang="en" href="{domain}{en_url}{query_suffix}" />')

    except NoReverseMatch:
        return ''
    finally:
        translation.activate(current_language)

    return mark_safe('\n    '.join(tags))


@register.simple_tag(takes_context=True)
def canonical_url(context):
    """Генерирует canonical URL для текущей страницы.

    Логика:
      - Хост: на проде всегда https://faw.uz, в DEBUG — текущий request.get_host().
      - Path: как есть в request.path.
      - Query: сохраняем контентные параметры (?category=samosval), убираем tracking (?utm_source=...).

    Для категорий каталога (/products/?category=samosval) canonical = /products/?category=samosval —
    категория считается отдельной страницей, со своим собственным SEO.
    """
    request = context.get('request')
    if not request:
        return ''

    domain = _canonical_base(request)
    path = request.path
    clean_qs = _clean_query_string(request.META.get('QUERY_STRING', ''))
    query_suffix = f'?{clean_qs}' if clean_qs else ''

    canonical = f"{domain}{path}{query_suffix}"

    return mark_safe(f'<link rel="canonical" href="{canonical}" />')