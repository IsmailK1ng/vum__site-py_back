# main/context_processors.py

from django.utils.translation import get_language
from django.conf import settings
from .models import PageMeta
import logging

logger = logging.getLogger('django')


def seo_meta(request):
    """
    Добавляет SEO мета-данные в контекст всех шаблонов.
    """
    
    full_path = request.get_full_path()
    path = request.path
    current_lang = get_language()
    
    path = path.strip('/')
    
    if path.startswith(current_lang + '/'):
        path = path[len(current_lang) + 1:]
    elif path.startswith(current_lang):
        path = path[len(current_lang):]
    
    path = path.lstrip('/')
    
    meta = None
    
    STATIC_PAGES = {
        '': 'home',
        'about': 'about',
        'contact': 'contact',
        'services': 'services',
        'lizing': 'lizing',
        'become-a-dealer': 'become-a-dealer',
        'jobs': 'jobs',
        'news': 'news',
        'dealers': 'dealers',
    }
    
    try:
        # ========== СТАТИЧЕСКИЕ СТРАНИЦЫ ==========
        if path in STATIC_PAGES:
            key = STATIC_PAGES[path]
            meta = PageMeta.objects.filter(
                model='Page',
                key=key,
                is_active=True
            ).first()
            
            if meta:
                logger.debug(f"[SEO] Найдено для '{key}' на языке {current_lang}")
            else:
                logger.warning(f"[SEO] НЕ найдено для '{key}' на языке {current_lang}")
        
        # ========== КАТАЛОГ С КАТЕГОРИЯМИ ==========
        elif path == 'products' and '?' in full_path:
            category = request.GET.get('category', '')
            
            if category:
                key = f'products_{category}'
                meta = PageMeta.objects.filter(
                    model='Page',
                    key=key,
                    is_active=True
                ).first()
                
                if meta:
                    logger.debug(f"[SEO] Категория: {key} на языке {current_lang}")
        
        # ========== ДИНАМИЧЕСКИЕ СТРАНИЦЫ - НОВОСТИ ==========
        elif path.startswith('news/') and path != 'news':
            slug = path.replace('news/', '').strip('/')
            
            if slug:
                from .models import News
                try:
                    news = News.objects.get(slug=slug, is_active=True)
                    
                    meta = PageMeta.objects.filter(
                        model='Post',
                        key=str(news.id),
                        is_active=True
                    ).first()
                    
                    if meta:
                        logger.debug(f"[SEO] Новость ID={news.id} на языке {current_lang}")
                
                except News.DoesNotExist:
                    logger.warning(f"[SEO] Новость не найдена: {slug}")
        
        # ========== ДИНАМИЧЕСКИЕ СТРАНИЦЫ - ПРОДУКТЫ ==========
        elif path.startswith('products/') and '?' not in full_path:
            slug = path.replace('products/', '').strip('/')
            
            if slug:
                from .models import Product
                try:
                    product = Product.objects.get(slug=slug, is_active=True)
                    
                    meta = PageMeta.objects.filter(
                        model='Product',
                        key=str(product.id),
                        is_active=True
                    ).first()
                    
                    if meta:
                        logger.debug(f"[SEO] Продукт ID={product.id} на языке {current_lang}")
                
                except Product.DoesNotExist:
                    logger.warning(f"[SEO] Продукт не найден: {slug}")
    
    except Exception as e:
        logger.error(f"[SEO] Ошибка: {str(e)}", exc_info=True)
        meta = None
    
    
    scheme = 'https' if not settings.DEBUG else request.scheme

    host = request.get_host()

    current_path = request.path
    
   
    current_page_url = f"{scheme}://{host}{current_path}"
    
    return {
        'page_meta': meta,
        'current_page_url': current_page_url  
    }