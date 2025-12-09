# main/serializers_base.py

from django.utils.translation import get_language


class LanguageSerializerMixin:
    """
    Базовый mixin для определения языка в serializers.
    
    Использует Django translation system вместо парсинга URL.
    Работает с ForceRussianMiddleware.
    """
    
    def get_current_language(self):
        """
        Получить текущий язык из Django translation system.
        
        Returns:
            str: Код языка ('uz', 'ru', 'en')
        
        Example:
            >>> self.get_current_language()
            'uz'
        """
        return get_language() or 'uz'