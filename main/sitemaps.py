from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from .models import Product, News, Vacancy

class LanguageSpecificSitemap(Sitemap):
    """Базовый класс для языковых sitemap"""
    protocol = 'https'
    
    def __init__(self, language):
        self.language = language
        super().__init__()
    
    def _get_url_prefix(self):
        """Префикс для URL в зависимости от языка"""
        if self.language == 'uz':
            return ''  # узбекский - без префикса (/)
        return f'/{self.language}'  # ru -> /ru/, en -> /en/


class StaticPagesSitemap(LanguageSpecificSitemap):
    """Статические страницы для конкретного языка"""
    
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
        prefix = self._get_url_prefix()
        if item == 'home':
            return f'{prefix}/' if prefix else '/'
        
        # Для остальных страниц
        base_url = reverse(item)
        return f'{prefix}{base_url}'
    
    def lastmod(self, item):
        return timezone.now()


class ProductsSitemap(LanguageSpecificSitemap):
    """Товары для конкретного языка"""
    
    def items(self):
        return Product.objects.filter(is_active=True)
    
    def location(self, obj):
        prefix = self._get_url_prefix()
        return f'{prefix}/products/{obj.slug}/'
    
    def lastmod(self, obj):
        return obj.updated_at


class NewsSitemap(LanguageSpecificSitemap):
    """Новости для конкретного языка"""
    
    def items(self):
        return News.objects.filter(is_active=True)
    
    def location(self, obj):
        prefix = self._get_url_prefix()
        return f'{prefix}/news/{obj.slug}/'
    
    def lastmod(self, obj):
        return obj.updated_at


class VacancySitemap(LanguageSpecificSitemap):
    """Вакансии для конкретного языка"""
    
    def items(self):
        return Vacancy.objects.filter(is_active=True)
    
    def location(self, obj):
        prefix = self._get_url_prefix()
        return f'{prefix}/jobs/'
    
    def lastmod(self, obj):
        return obj.updated_at


# ========== ЭКСПОРТ ДЛЯ КАЖДОГО ЯЗЫКА ==========
def get_sitemaps_for_language(language):
    """Создает sitemap для конкретного языка"""
    return {
        'static': StaticPagesSitemap(language),
        'products': ProductsSitemap(language),
        'news': NewsSitemap(language),
        'vacancies': VacancySitemap(language),
    }