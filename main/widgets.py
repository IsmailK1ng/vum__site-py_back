"""
Кастомные виджеты для Django Admin с иконками подсказок
"""

from django import forms
from django.utils.safestring import mark_safe


class HelpIconWidget:
    """
    Миксин для добавления иконки помощи к виджетам
    """
    
    def __init__(self, *args, help_text='', **kwargs):
        self.help_text_popup = help_text
        super().__init__(*args, **kwargs)
    
    def render(self, name, value, attrs=None, renderer=None):
        """Рендерим виджет + иконку помощи"""
        # Получаем обычный HTML виджета
        widget_html = super().render(name, value, attrs, renderer)
        
        # Если есть текст подсказки, добавляем иконку
        if self.help_text_popup:
            help_icon = f'''
            <span class="seo-help-icon" data-help="{self.help_text_popup}">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
            </span>
            '''
            widget_html = mark_safe(f'{widget_html} {help_icon}')
        
        return widget_html


class SelectWithHelp(HelpIconWidget, forms.Select):
    """Select dropdown с иконкой помощи"""
    pass


class TextInputWithHelp(HelpIconWidget, forms.TextInput):
    """Text input с иконкой помощи"""
    pass


class TextareaWithHelp(HelpIconWidget, forms.Textarea):
    """Textarea с иконкой помощи"""
    pass


class URLInputWithHelp(HelpIconWidget, forms.URLInput):
    """URL input с иконкой помощи"""
    pass


class FileInputWithHelp(HelpIconWidget, forms.ClearableFileInput):
    """File input с иконкой помощи"""
    pass