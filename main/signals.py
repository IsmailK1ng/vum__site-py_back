# main/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import News, Product, PageMeta


# ========== АВТОЗАПОЛНЕНИЕ og_url ДЛЯ PageMeta ==========

@receiver(post_save, sender=PageMeta)
def fill_og_urls(sender, instance, created, **kwargs):
    """
    Автоматически заполняет og_url_uz, og_url_ru, og_url_en
    при создании или если они пустые.
    """
    # Проверяем: нужно ли заполнять?
    if not created and instance.og_url_uz:
        # Уже заполнено и это не новая запись
        return
    
    base_url = 'https://faw.uz'
    
    # ========== ДЛЯ СТАТИЧЕСКИХ СТРАНИЦ ==========
    if instance.model == 'Page':
        # Обычные статические страницы
        static_pages = {
            'home': '/',
            'about': '/about/',
            'contact': '/contact/',
            'services': '/services/',
            'lizing': '/lizing/',
            'become-a-dealer': '/become-a-dealer/',
            'jobs': '/jobs/',
            'news': '/news/',
            'dealers': '/dealers/',
        }
        
        # Проверяем: это обычная страница?
        if instance.key in static_pages:
            path = static_pages[instance.key]
            
            # УЗ - без префикса
            instance.og_url_uz = f"{base_url}{path}"
            
            # RU - с префиксом /ru/
            instance.og_url_ru = f"{base_url}/ru{path}"
            
            # EN - с префиксом /en/
            instance.og_url_en = f"{base_url}/en{path}"
        
        # Проверяем: это категория продуктов?
        elif instance.key.startswith('products_'):
            # Извлекаем slug категории
            category = instance.key.replace('products_', '')
            path = f"/products/?category={category}"
            
            # УЗ
            instance.og_url_uz = f"{base_url}{path}"
            
            # RU
            instance.og_url_ru = f"{base_url}/ru{path}"
            
            # EN
            instance.og_url_en = f"{base_url}/en{path}"
    
    # ========== ДЛЯ НОВОСТЕЙ ==========
    elif instance.model == 'Post':
        try:
            news = News.objects.get(id=int(instance.key))
            path = f"/news/{news.slug}/"
            
            # УЗ
            instance.og_url_uz = f"{base_url}{path}"
            
            # RU
            instance.og_url_ru = f"{base_url}/ru{path}"
            
            # EN
            instance.og_url_en = f"{base_url}/en{path}"
        except (News.DoesNotExist, ValueError):
            pass
    
    # ========== ДЛЯ ПРОДУКТОВ ==========
    elif instance.model == 'Product':
        try:
            product = Product.objects.get(id=int(instance.key))
            path = f"/products/{product.slug}/"
            
            # УЗ
            instance.og_url_uz = f"{base_url}{path}"
            
            # RU
            instance.og_url_ru = f"{base_url}/ru{path}"
            
            # EN
            instance.og_url_en = f"{base_url}/en{path}"
        except (Product.DoesNotExist, ValueError):
            pass
    
    # Сохраняем (без вызова signal снова)
    PageMeta.objects.filter(pk=instance.pk).update(
        og_url_uz=instance.og_url_uz,
        og_url_ru=instance.og_url_ru,
        og_url_en=instance.og_url_en
    )


# ========== SIGNAL ДЛЯ НОВОСТЕЙ ==========

@receiver(post_save, sender=News)
def create_seo_for_news(sender, instance, created, **kwargs):
    if created:
        PageMeta.objects.get_or_create(
            model='Post',
            key=str(instance.id),
            defaults={
                'is_active': False,
                'title': '',
                'description': '',
                'keywords': '',
                'og_type': 'article',
            }
        )


# ========== SIGNAL ДЛЯ ПРОДУКТОВ ==========

@receiver(post_save, sender=Product)
def create_seo_for_product(sender, instance, created, **kwargs):
    if created:
        PageMeta.objects.get_or_create(
            model='Product',
            key=str(instance.id),
            defaults={
                'is_active': False,
                'title': '',
                'description': '',
                'keywords': '',
                'og_type': 'product',
            }
        )