from modeltranslation.translator import register, TranslationOptions
from .models import News, NewsBlock

@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'desc')

@register(NewsBlock)
class NewsBlockTranslationOptions(TranslationOptions):
    fields = ('text',)
