from django.utils import translation
from django.conf import settings
from django.http import HttpResponseRedirect
from urllib.parse import urlencode


class ForceRussianMiddleware:
    """Принудительно устанавливает русский язык для админки, узбекский для сайта"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Для админки принудительно русский
        if request.path.startswith('/admin/'):
            translation.activate('ru')
            request.LANGUAGE_CODE = 'ru'
        else:
            # Для сайта - проверяем есть ли сохранённый язык
            # Используем правильную константу для Django 5.x
            saved_language = request.session.get('_language')  # ← Изменено!
            cookie_language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, None)
            
            # Приоритет: сессия > cookie > узбекский по умолчанию
            language = saved_language or cookie_language or 'uz'
            
            # Проверяем что язык поддерживается
            if language in [lang[0] for lang in settings.LANGUAGES]:
                translation.activate(language)
                request.LANGUAGE_CODE = language
            else:
                translation.activate('uz')
                request.LANGUAGE_CODE = 'uz'
        
        response = self.get_response(request)
        
        # Устанавливаем заголовок Content-Language
        if request.path.startswith('/admin/'):
            response['Content-Language'] = 'ru'
        else:
            response['Content-Language'] = request.LANGUAGE_CODE
        
        return response


class RefreshUserPermissionsMiddleware:
    """
    Лёгкий middleware: просто сбрасывает кэш прав при каждом запросе.
    Django автоматически перезагрузит права из БД при первом обращении.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Сбрасываем кэш прав только для обычных админов (не суперюзеров)
        if request.user.is_authenticated and not request.user.is_superuser:
            # Удаляем кэшированные права
            if hasattr(request.user, '_perm_cache'):
                delattr(request.user, '_perm_cache')
            if hasattr(request.user, '_user_perm_cache'):
                delattr(request.user, '_user_perm_cache')
            if hasattr(request.user, '_group_perm_cache'):
                delattr(request.user, '_group_perm_cache')
        
        response = self.get_response(request)
        return response

class PreserveFiltersMiddleware:
    """Сохранение фильтров ContactForm"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import logging
        logger = logging.getLogger('django')
        
        if request.path == '/admin/main/contactform/' and request.method == 'GET':
            logger.error(f"🔍 MIDDLEWARE: path={request.path}, GET={dict(request.GET)}")
            
            has_e = 'e' in request.GET
            has_filters = any(k != 'e' for k in request.GET.keys())
            
            logger.error(f"🔍 MIDDLEWARE: has_e={has_e}, has_filters={has_filters}")
            
            # ✅ Если ТОЛЬКО e=1 - убираем его и добавляем сохраненные фильтры
            if has_e and not has_filters:
                saved = request.session.get('contactform_filters')
                logger.error(f"📂 MIDDLEWARE: Retrieved filters: {saved}")
                
                if saved:
                    # НЕ УДАЛЯЕМ! Просто редиректим
                    params = [f"{key}={value}" for key, values in saved.items() for value in values]
                    new_url = f"{request.path}?{'&'.join(params)}"
                    
                    logger.error(f"🔄 MIDDLEWARE: Redirecting to {new_url}")
                    return HttpResponseRedirect(new_url)
            
            # ✅ Сохраняем фильтры БЕЗ e=1 (перезаписываем)
            elif not has_e and has_filters:
                request.session['contactform_filters'] = dict(request.GET.lists())
                request.session.modified = True
                logger.error(f"💾 MIDDLEWARE: Saved filters: {request.session['contactform_filters']}")

        return self.get_response(request)