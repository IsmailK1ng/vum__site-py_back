from django.utils import translation
from django.contrib.auth import get_user_model


class ForceRussianMiddleware:
    """Принудительно устанавливает русский язык для админки"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Для всех запросов в админку принудительно русский
        if request.path.startswith('/admin/'):
            translation.activate('ru')
            request.LANGUAGE_CODE = 'ru'
        
        response = self.get_response(request)
        
        # Устанавливаем заголовок Content-Language
        if request.path.startswith('/admin/'):
            response['Content-Language'] = 'ru'
        
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