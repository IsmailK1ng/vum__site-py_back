from django.utils import translation
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
import logging

logger = logging.getLogger('django')


class WWWRedirectMiddleware:
    """
    Редирект с www.faw.uz на faw.uz (301)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        
        # Редирект только в продакшене
        if not settings.DEBUG and host.startswith('www.'):
            new_host = host[4:]
            new_url = f"{request.scheme}://{new_host}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(new_url)
        
        return self.get_response(request)


class LanguageCookieMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        

        current_language = translation.get_language()
        
        cookie_language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        

        if cookie_language != current_language:
            response.set_cookie(
                key=settings.LANGUAGE_COOKIE_NAME,
                value=current_language,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
        
        return response

class ForceRussianMiddleware:
    """Принудительно устанавливает русский язык для админки, узбекский для сайта"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            # Admin всегда на русском
            if request.path.startswith('/admin/'):
                translation.activate('ru')
                request.LANGUAGE_CODE = 'ru'
            
            # ✅ API: определяем язык из URL
            elif request.path.startswith('/api/'):
                language = 'uz'  # default
                
                # Проверяем префикс языка в URL
                if '/api/uz/' in request.path:
                    language = 'uz'
                elif '/api/ru/' in request.path:
                    language = 'ru'
                elif '/api/en/' in request.path:
                    language = 'en'
                elif '/api/kg/' in request.path:
                    saved_language = request.session.get('_language')
                    cookie_language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
                    language = saved_language or cookie_language or 'ky'
                
                translation.activate(language)
                request.LANGUAGE_CODE = language
            
            else:
                language = 'uz'  
                if request.path.startswith('/ru/'):
                    language = 'ru'
                elif request.path.startswith('/en/'):
                    language = 'en'
                else:
                    # Fallback на session/cookie
                    saved_language = request.session.get('_language')
                    cookie_language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
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
        
