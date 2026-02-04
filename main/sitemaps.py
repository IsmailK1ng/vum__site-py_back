from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from .models import Product, News

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


class CategorySitemap(LanguageSpecificSitemap):
    """Категории товаров"""
    
    def items(self):
        return [
            ('samosval', 'Samosvallar'),
            ('maxsus', 'Maxsus texnika'),
            ('furgon', 'Avtofurgonlar'),
            ('shassi', 'Shassilar'),
            ('tiger_v', 'Tiger V'),
            ('tiger_vh', 'Tiger VH'),
            ('tiger_vr', 'Tiger VR'),
        ]
    
    def location(self, item):
        category_slug, category_name = item
        prefix = self._get_url_prefix()
        return f'{prefix}/products/?category={category_slug}'
    
    def lastmod(self, item):
        from datetime import datetime
        
        category_slug, _ = item
        latest_product = Product.objects.filter(
            category=category_slug,
            is_active=True
        ).order_by('-updated_at').first()
        
        if latest_product:
            return latest_product.updated_at
        
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


def get_sitemaps_for_language(language):
    """Создает sitemap для конкретного языка"""
    return {
        'static': StaticPagesSitemap(language),
        'categories': CategorySitemap(language),
        'products': ProductsSitemap(language),
        'news': NewsSitemap(language),
    }