# main/templatetags/seo_tags.py

from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def hreflang_tags(context):
    """
    Генерирует hreflang теги для текущей страницы.
    
    Использование в шаблоне:
    {% load seo_tags %}
    {% hreflang_tags %}
    """
    request = context.get('request')
    if not request:
        return ''
    
    url_name = request.resolver_match.url_name if request.resolver_match else None
    if not url_name:
        return ''
    
    domain = request.build_absolute_uri('/').rstrip('/')
    url_kwargs = request.resolver_match.kwargs if request.resolver_match else {}
    
    tags = []
    
    try:
        # Узбекский (дефолтный, без префикса)
        uz_url = reverse(url_name, kwargs=url_kwargs)
        tags.append(f'<link rel="alternate" hreflang="uz" href="{domain}{uz_url}" />')
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{domain}{uz_url}" />')
        
        # Русский (с префиксом /ru/)
        ru_url = f"/ru{reverse(url_name, kwargs=url_kwargs)}"
        tags.append(f'<link rel="alternate" hreflang="ru" href="{domain}{ru_url}" />')
        
        # Английский (с префиксом /en/)
        en_url = f"/en{reverse(url_name, kwargs=url_kwargs)}"
        tags.append(f'<link rel="alternate" hreflang="en" href="{domain}{en_url}" />')
        
    except NoReverseMatch:
        return ''
    
    return mark_safe('\n    '.join(tags))


@register.simple_tag(takes_context=True)
def canonical_url(context):

    request = context.get('request')
    if not request:
        return ''
    
    # Получаем чистый URL без параметров
    scheme = request.scheme  
    host = request.get_host()  
    path = request.path  
    
    canonical = f"{scheme}://{host}{path}"
    
    return mark_safe(f'<link rel="canonical" href="{canonical}" />')