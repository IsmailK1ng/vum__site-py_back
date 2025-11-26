from django.utils import translation
from django.conf import settings
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger('django')


class ForceRussianMiddleware:
    """Принудительно устанавливает русский язык для админки, узбекский для сайта"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            if request.path.startswith('/admin/'):
                translation.activate('ru')
                request.LANGUAGE_CODE = 'ru'
            else:
                saved_language = request.session.get('_language')
                cookie_language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, None)
                
                language = saved_language or cookie_language or 'uz'
                
                if language in [lang[0] for lang in settings.LANGUAGES]:
                    translation.activate(language)
                    request.LANGUAGE_CODE = language
                else:
                    translation.activate('uz')
                    request.LANGUAGE_CODE = 'uz'
            
            response = self.get_response(request)
            
            if request.path.startswith('/admin/'):
                response['Content-Language'] = 'ru'
            else:
                response['Content-Language'] = request.LANGUAGE_CODE
            
            return response
        
        except Exception as e:
            logger.error(f"Ошибка в ForceRussianMiddleware: {str(e)}", exc_info=True)
            translation.activate('uz')
            return self.get_response(request)


class RefreshUserPermissionsMiddleware:
    """Сбрасывает кэш прав при каждом запросе"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            if request.user.is_authenticated and not request.user.is_superuser:
                if hasattr(request.user, '_perm_cache'):
                    delattr(request.user, '_perm_cache')
                if hasattr(request.user, '_user_perm_cache'):
                    delattr(request.user, '_user_perm_cache')
                if hasattr(request.user, '_group_perm_cache'):
                    delattr(request.user, '_group_perm_cache')
            
            return self.get_response(request)
        
        except Exception as e:
            logger.error(f"Ошибка в RefreshUserPermissionsMiddleware: {str(e)}", exc_info=True)
            return self.get_response(request)


class PreserveFiltersMiddleware:
    """Сохранение фильтров ContactForm"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.path == '/admin/main/contactform/' and request.method == 'GET':
                
                has_e = 'e' in request.GET
                has_filters = any(k != 'e' for k in request.GET.keys())
                
                if has_e and not has_filters:
                    saved = request.session.get('contactform_filters')
                    
                    if saved:
                        params = [f"{key}={value}" for key, values in saved.items() for value in values]
                        new_url = f"{request.path}?{'&'.join(params)}"
                        return HttpResponseRedirect(new_url)
                
                elif not has_e and has_filters:
                    request.session['contactform_filters'] = dict(request.GET.lists())
                    request.session.modified = True

            return self.get_response(request)
        
        except Exception as e:
            logger.error(f"Ошибка в PreserveFiltersMiddleware: {str(e)}", exc_info=True)
            return self.get_response(request)