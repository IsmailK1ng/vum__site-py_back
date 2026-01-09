"""
Context Processors для добавления данных во все шаблоны
"""

from django.utils.translation import get_language
from .models import PageMeta
import logging

logger = logging.getLogger('django')


def seo_meta(request):
    """
    Добавляет SEO мета-данные в контекст всех шаблонов.
    
    Автоматически определяет тип страницы по URL и загружает соответствующие мета-данные.
    """
    
    path = request.path.strip('/')
    current_lang = get_language()
    
    # Убираем префикс языка
    if path.startswith(f'{current_lang}/'):
        path = path[len(current_lang)+1:]
    
    meta = None
    
    try:
        # ========== СТАТИЧЕСКИЕ СТРАНИЦЫ ==========
        if path == '':
            # Главная
            meta = PageMeta.objects.filter(
                model='Page', key='home', is_active=True
            ).first()
        
        elif path == 'about':
            meta = PageMeta.objects.filter(
                model='Page', key='about', is_active=True
            ).first()
        
        elif path == 'contact':
            meta = PageMeta.objects.filter(
                model='Page', key='contact', is_active=True
            ).first()
        
        elif path == 'services':
            meta = PageMeta.objects.filter(
                model='Page', key='services', is_active=True
            ).first()
        
        elif path == 'lizing':
            meta = PageMeta.objects.filter(
                model='Page', key='lizing', is_active=True
            ).first()
        
        elif path == 'become-a-dealer':
            meta = PageMeta.objects.filter(
                model='Page', key='become-a-dealer', is_active=True
            ).first()
        
        elif path == 'jobs':
            meta = PageMeta.objects.filter(
                model='Page', key='jobs', is_active=True
            ).first()
        
        elif path == 'news':
            # Список новостей
            meta = PageMeta.objects.filter(
                model='Page', key='news', is_active=True
            ).first()
        
        elif path == 'dealers':
            # Список дилеров
            meta = PageMeta.objects.filter(
                model='Page', key='dealers', is_active=True
            ).first()
        
        # ========== КАТАЛОГ С КАТЕГОРИЯМИ ==========
        elif path.startswith('products') and '?' in request.get_full_path():
            # Каталог с категорией: /products/?category=samosval
            full_path = request.get_full_path()
            
            if 'category=samosval' in full_path:
                meta = PageMeta.objects.filter(
                    model='Page', key='products_samosval', is_active=True
                ).first()
            
            elif 'category=maxsus' in full_path:
                meta = PageMeta.objects.filter(
                    model='Page', key='products_maxsus', is_active=True
                ).first()
            
            elif 'category=furgon' in full_path:
                meta = PageMeta.objects.filter(
                    model='Page', key='products_furgon', is_active=True
                ).first()
            
            elif 'category=shassi' in full_path:
                meta = PageMeta.objects.filter(
                    model='Page', key='products_shassi', is_active=True
                ).first()
            
            elif 'category=tiger_v' in full_path:
                meta = PageMeta.objects.filter(
                    model='Page', key='products_tiger_v', is_active=True
                ).first()
            
            elif 'category=tiger_vh' in full_path:
                meta = PageMeta.objects.filter(
                    model='Page', key='products_tiger_vh', is_active=True
                ).first()
            
            elif 'category=tiger_vr' in full_path:
                meta = PageMeta.objects.filter(
                    model='Page', key='products_tiger_vr', is_active=True
                ).first()
        
        # ========== ДИНАМИЧЕСКИЕ СТРАНИЦЫ - НОВОСТИ ==========
        elif path.startswith('news/') and path != 'news':
            # Детальная новость: /news/muxlisa-ai-statistika/
            slug = path.replace('news/', '').strip('/')
            
            if slug:
                from .models import News
                try:
                    news = News.objects.get(slug=slug, is_active=True)
                    
                    # Ищем SEO по ID новости
                    meta = PageMeta.objects.filter(
                        model='Post',
                        key=str(news.id),  # ← ID новости!
                        is_active=True
                    ).first()
                    
                    if meta:
                        logger.debug(f"SEO найдено для новости: {news.title} (ID={news.id})")
                
                except News.DoesNotExist:
                    logger.warning(f"Новость не найдена: {slug}")
        
        # ========== ДИНАМИЧЕСКИЕ СТРАНИЦЫ - ПРОДУКТЫ ==========
        elif path.startswith('products/') and '?' not in request.get_full_path():
            # Детальный продукт: /products/avtosamosval-faw-tiger-v/
            slug = path.replace('products/', '').strip('/')
            
            if slug:
                from .models import Product
                try:
                    product = Product.objects.get(slug=slug, is_active=True)
                    
                    # Ищем SEO по ID продукта
                    meta = PageMeta.objects.filter(
                        model='Product',
                        key=str(product.id),  # ← ID продукта!
                        is_active=True
                    ).first()
                    
                    if meta:
                        logger.debug(f"SEO найдено для продукта: {product.title} (ID={product.id})")
                
                except Product.DoesNotExist:
                    logger.warning(f"Продукт не найден: {slug}")
    
    except Exception as e:
        logger.error(f"Ошибка в seo_meta: {str(e)}", exc_info=True)
        meta = None
    
    return {
        'page_meta': meta
    }