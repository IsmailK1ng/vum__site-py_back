from django.contrib.sitemaps import Sitemap
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
            return ''
        return f'/{self.language}'


class StaticPagesSitemap(LanguageSpecificSitemap):
    """Статические страницы"""
    
    def items(self):
        return [
            ('home', '/'),
            ('about', '/about/'),
            ('contact', '/contact/'),
            ('services', '/services/'),
            ('products', '/products/'),
            ('become_a_dealer', '/become-a-dealer/'),
            ('lizing', '/lizing/'),
            ('news', '/news/'),
            ('dealers', '/dealers/'),
            ('jobs', '/jobs/'),
        ]
    
    def location(self, item):
        name, path = item
        prefix = self._get_url_prefix()
        return f'{prefix}{path}'
    
    def lastmod(self, item):
        from datetime import datetime
        return datetime.now(timezone.get_current_timezone())


class ProductsSitemap(LanguageSpecificSitemap):
    """Товары"""
    
    def items(self):
        return Product.objects.filter(is_active=True)
    
    def location(self, obj):
        prefix = self._get_url_prefix()
        return f'{prefix}/products/{obj.slug}/'
    
    def lastmod(self, obj):
        from datetime import datetime, time
        if isinstance(obj.updated_at, datetime):
            return obj.updated_at
        # Если это DateField, добавляем время
        return datetime.combine(obj.updated_at, time.min, tzinfo=timezone.get_current_timezone())


class NewsSitemap(LanguageSpecificSitemap):
    """Новости"""
    
    def items(self):
        return News.objects.filter(is_active=True)
    
    def location(self, obj):
        prefix = self._get_url_prefix()
        return f'{prefix}/news/{obj.slug}/'
    
    def lastmod(self, obj):
        from datetime import datetime, time
        if isinstance(obj.updated_at, datetime):
            return obj.updated_at
        return datetime.combine(obj.updated_at, time.min, tzinfo=timezone.get_current_timezone())


class VacancySitemap(LanguageSpecificSitemap):
    """Вакансии"""
    
    def items(self):
        return Vacancy.objects.filter(is_active=True)
    
    def location(self, obj):
        prefix = self._get_url_prefix()
        return f'{prefix}/jobs/'
    
    def lastmod(self, obj):
        from datetime import datetime, time
        if isinstance(obj.updated_at, datetime):
            return obj.updated_at
        return datetime.combine(obj.updated_at, time.min, tzinfo=timezone.get_current_timezone())


def get_sitemaps_for_language(language):
    """Создает sitemap для конкретного языка"""
    return {
        'static': StaticPagesSitemap(language),
        'products': ProductsSitemap(language),
        'news': NewsSitemap(language),
        'vacancies': VacancySitemap(language),
    }