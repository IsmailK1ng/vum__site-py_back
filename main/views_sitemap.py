from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.sitemaps.views import sitemap as django_sitemap
from .sitemaps import get_sitemaps_for_language

def sitemap_index(request):
    """Главный sitemap-индекс со списком языковых sitemap"""
    
    base_url = request.build_absolute_uri('/').rstrip('/')
    
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>{base_url}/sitemap-uz.xml</loc>
    <lastmod>{timezone.now().isoformat()}</lastmod>
  </sitemap>
  <sitemap>
    <loc>{base_url}/sitemap-ru.xml</loc>
    <lastmod>{timezone.now().isoformat()}</lastmod>
  </sitemap>
  <sitemap>
    <loc>{base_url}/sitemap-en.xml</loc>
    <lastmod>{timezone.now().isoformat()}</lastmod>
  </sitemap>
</sitemapindex>'''
    
    return HttpResponse(xml_content, content_type='application/xml')


def sitemap_uz(request):
    """Узбекский sitemap"""
    sitemaps = get_sitemaps_for_language('uz')
    return django_sitemap(request, sitemaps=sitemaps)


def sitemap_ru(request):
    """Русский sitemap"""
    sitemaps = get_sitemaps_for_language('ru')
    return django_sitemap(request, sitemaps=sitemaps)


def sitemap_en(request):
    """Английский sitemap"""
    sitemaps = get_sitemaps_for_language('en')
    return django_sitemap(request, sitemaps=sitemaps)