from django.utils import translation


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