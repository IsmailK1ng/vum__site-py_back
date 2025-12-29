from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, News, Vacancy

class StaticPagesSitemap(Sitemap):
    """Статические страницы"""
    protocol = 'https'
    priority = 1.0
    changefreq = 'weekly'
    
    def items(self):
        return [
            'home',
            'about',
            'contact',
            'services',
            'products',
            'become_a_dealer',
            'lizing',
            'news',
            'dealers',
            'jobs',
        ]
    
    def location(self, item):
        return reverse(item)


class ProductsSitemap(Sitemap):
    """Все модели грузовиков"""
    protocol = 'https'
    changefreq = "monthly"
    priority = 0.9
    
    def items(self):
        return Product.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f'/products/{obj.slug}/'


class NewsSitemap(Sitemap):
    """Все новости"""
    protocol = 'https'
    changefreq = "weekly"
    priority = 0.7
    
    def items(self):
        return News.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f'/news/{obj.slug}/'


class VacancySitemap(Sitemap):
    """Все вакансии"""
    protocol = 'https'
    changefreq = "monthly"
    priority = 0.6
    
    def items(self):
        return Vacancy.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return '/jobs/'


# ========== ЭКСПОРТ ==========
sitemaps = {
    'static': StaticPagesSitemap,
    'products': ProductsSitemap,
    'news': NewsSitemap,
    'vacancies': VacancySitemap,
}