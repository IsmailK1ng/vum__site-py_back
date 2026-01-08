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
    
    # Получаем текущий путь без языкового префикса
    path = request.path
    
    # Убираем языковые префиксы /uz/, /ru/, /en/
    for lang_prefix in ['/uz/', '/ru/', '/en/']:
        if path.startswith(lang_prefix):
            path = path[3:]  # Убираем /uz/, /ru/, /en/
            break
    
    path = path.strip('/')
    
    meta = None
    
    try:
        # ========== СТАТИЧЕСКИЕ СТРАНИЦЫ ==========
        static_pages = {
            '': 'home',                          # Главная
            'about': 'about',                    # О нас
            'contact': 'contact',                # Контакты
            'products': 'products',              # Каталог продуктов
            'dealers': 'dealers',                # Дилеры
            'jobs': 'jobs',                      # Вакансии
            'lizing': 'lizing',                  # Лизинг
            'become-a-dealer': 'become-a-dealer',# Стать дилером
            'news': 'news',                      # Список новостей
        }
        
        if path in static_pages:
            # Ищем мета для статической страницы
            meta = PageMeta.objects.filter(
                model='Page',
                key=static_pages[path],
                is_active=True
            ).first()
            
            if meta:
                logger.debug(f"✅ SEO: Найдена мета для статической страницы '{path}' (key={static_pages[path]})")
        
        # ========== ДИНАМИЧЕСКИЕ СТРАНИЦЫ - НОВОСТИ ==========
        elif path.startswith('news/') and path != 'news':
            # Извлекаем slug новости: news/kakaya-to-novost/
            slug = path.replace('news/', '').strip('/')
            
            if slug:
                # Пытаемся найти новость по slug
                from .models import News
                try:
                    news = News.objects.get(slug=slug, is_active=True)
                    
                    # Ищем мета по ID новости
                    meta = PageMeta.objects.filter(
                        model='Post',
                        key=str(news.id),
                        is_active=True
                    ).first()
                    
                    if meta:
                        logger.debug(f"✅ SEO: Найдена мета для новости '{news.title}' (ID={news.id})")
                    else:
                        logger.debug(f"⚠️ SEO: Мета не найдена для новости ID={news.id}, используется fallback")
                
                except News.DoesNotExist:
                    logger.warning(f"❌ SEO: Новость с slug='{slug}' не найдена")
        
        # ========== ДИНАМИЧЕСКИЕ СТРАНИЦЫ - ПРОДУКТЫ ==========
        elif path.startswith('products/') and path != 'products':
            # Извлекаем slug продукта: products/tiger-vh/
            slug = path.replace('products/', '').strip('/')
            
            if slug:
                # Ищем мета по slug продукта
                meta = PageMeta.objects.filter(
                    model='Product',
                    key=slug,
                    is_active=True
                ).first()
                
                if meta:
                    logger.debug(f"✅ SEO: Найдена мета для продукта '{slug}'")
                else:
                    logger.debug(f"⚠️ SEO: Мета не найдена для продукта '{slug}', используется fallback")
        
        # ========== ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ (только в DEBUG режиме) ==========
        if meta:
            logger.info(f"✅ SEO Meta загружена: {meta.model} - {meta.key} - {meta.title[:50]}")
        else:
            logger.debug(f"⚠️ SEO Meta не найдена для пути: {request.path}")
    
    except Exception as e:
        logger.error(f"❌ Ошибка в seo_meta context processor: {str(e)}", exc_info=True)
        meta = None
    
    return {
        'page_meta': meta
    }