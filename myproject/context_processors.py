from django.utils import translation

def html_lang(request):
    lang = translation.get_language() or 'uz'

    mapping = {
        'uz': 'uz-UZ',
        'ru': 'ru-UZ',
        'en': 'en-UZ',
    }

    return {
        'HTML_LANG': mapping.get(lang, 'uz-UZ')
    }
