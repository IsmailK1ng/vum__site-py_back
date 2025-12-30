from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime
from .sitemaps import get_sitemaps_for_language


def sitemap_index(request):
    """Главный sitemap-индекс"""
    base_url = request.build_absolute_uri('/').rstrip('/')
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>{base_url}/sitemap-uz.xml</loc>
    <lastmod>{now}</lastmod>
  </sitemap>
  <sitemap>
    <loc>{base_url}/sitemap-ru.xml</loc>
    <lastmod>{now}</lastmod>
  </sitemap>
  <sitemap>
    <loc>{base_url}/sitemap-en.xml</loc>
    <lastmod>{now}</lastmod>
  </sitemap>
</sitemapindex>'''
    
    return HttpResponse(xml_content, content_type='application/xml')


def _generate_sitemap_xml(request, sitemaps):
    """Генерирует XML для языкового sitemap с правильным форматом дат"""
    urls = []
    
    for section, site in sitemaps.items():
        for item in site.items():
            loc = site.get_protocol() + '://' + request.get_host() + site.location(item)
            
            # Получаем lastmod и форматируем в ISO с миллисекундами
            lastmod_date = site.lastmod(item) if hasattr(site, 'lastmod') else None
            if lastmod_date:
                if isinstance(lastmod_date, datetime):
                    lastmod = lastmod_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                else:
                    # Если это date (не datetime), добавляем время
                    lastmod = datetime.combine(lastmod_date, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            else:
                lastmod = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            
            urls.append({
                'loc': loc,
                'lastmod': lastmod
            })
    
    # Генерируем XML
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">')
    
    for url in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{url["loc"]}</loc>')
        xml_lines.append(f'    <lastmod>{url["lastmod"]}</lastmod>')
        xml_lines.append('  </url>')
    
    xml_lines.append('</urlset>')
    
    return '\n'.join(xml_lines)


def sitemap_uz(request):
    """Узбекский sitemap"""
    sitemaps = get_sitemaps_for_language('uz')
    xml_content = _generate_sitemap_xml(request, sitemaps)
    return HttpResponse(xml_content, content_type='application/xml')


def sitemap_ru(request):
    """Русский sitemap"""
    sitemaps = get_sitemaps_for_language('ru')
    xml_content = _generate_sitemap_xml(request, sitemaps)
    return HttpResponse(xml_content, content_type='application/xml')


def sitemap_en(request):
    """Английский sitemap"""
    sitemaps = get_sitemaps_for_language('en')
    xml_content = _generate_sitemap_xml(request, sitemaps)
    return HttpResponse(xml_content, content_type='application/xml')