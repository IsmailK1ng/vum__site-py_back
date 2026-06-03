from django.utils import translation
from django.utils.translation.trans_real import (
    parse_accept_lang_header,
    get_supported_language_variant,
)
from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
import logging

logger = logging.getLogger('django')


class WWWRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG:
            return self.get_response(request)

        host = request.META.get('HTTP_HOST', '').lower()

        if host == 'www.faw.uz':
            return HttpResponsePermanentRedirect(
                'https://faw.uz' + request.get_full_path()
            )

        return self.get_response(request)



class ForceRussianMiddleware:
    """Локализация для админки и API.

    - /admin/   → принудительно русский (админка одноязычная).
    - /api/uz|ru|en/ → язык по префиксу URL.
    - /api/kg/  → язык из сессии/cookie, fallback 'ky'.
    - /api/...  (без префикса) → 'uz' по умолчанию.

    Для пользовательских страниц сайта это middleware ничего не делает —
    язык уже корректно установлен стандартным django.middleware.locale.LocaleMiddleware
    (выше в стеке) на основе URL-префикса (i18n_patterns), cookie и Accept-Language.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.path.startswith('/admin/'):
                translation.activate('ru')
                request.LANGUAGE_CODE = 'ru'

            elif request.path.startswith('/api/'):
                language = 'uz'
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

            # Для страниц сайта (не admin/api) — никаких манипуляций.
            # LocaleMiddleware уже сделал всё что нужно.

            response = self.get_response(request)

            if request.path.startswith('/admin/'):
                response['Content-Language'] = 'ru'
            else:
                response['Content-Language'] = getattr(request, 'LANGUAGE_CODE', 'uz')

            return response

        except Exception as e:
            logger.error(f"Ошибка в ForceRussianMiddleware: {str(e)}", exc_info=True)
            return self.get_response(request)


class AutoLanguageMiddleware:
    """Авто-определение языка и синхронизация cookie с URL-префиксом.

    Сценарии:

    1. URL **без** префикса (например /, /about/):
       - cookie указывает на non-default язык (ru/en) → редирект на /<lang><path>
       - cookie нет → определяем по Accept-Language; если ru/en → редирект + cookie
       - cookie=uz или язык не распознан → остаёмся UZ; cookie не трогаем

    2. URL **с** префиксом (/ru/..., /en/...):
       - cookie отличается от URL-префикса → обновляем cookie под текущий язык
       - так юзер открывший /ru/about/ из закладки получит /ru/ при последующем заходе на /

    3. Пропускаем (никаких манипуляций):
       - не-GET запросы (POST/PUT и т.д.)
       - боты (Googlebot, YandexBot, ...) — должны индексировать страницы как есть
       - служебные URL: /admin/, /api/, /set-language/, /sitemap*, /robots.txt, /media/, /static/, /nested_admin/, /dealer/
       - "невалидные" UZ-префикс URL'ы (/uz/...) — Django их 404-ит, не трогаем
    """

    NON_DEFAULT_LANGS = ('ru', 'en')

    SKIP_PATHS = (
        '/admin/', '/api/', '/set-language/',
        '/sitemap', '/robots.txt',
        '/media/', '/static/',
        '/nested_admin/', '/dealer/',
        '/uz/',  # невалидный префикс в нашей схеме (prefix_default_language=False)
    )

    BOT_PATTERNS = (
        'bot', 'crawler', 'spider', 'slurp',
        'yandex', 'googlebot', 'bingbot', 'duckduck',
        'facebookexternalhit', 'twitterbot', 'linkedinbot',
        'telegrambot', 'whatsapp', 'applebot',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def _is_bot(self, request):
        ua = request.META.get('HTTP_USER_AGENT', '').lower()
        if not ua:
            return True
        return any(pattern in ua for pattern in self.BOT_PATTERNS)

    def _should_skip(self, request):
        if request.method != 'GET':
            return True
        path = request.path
        return any(path.startswith(p) for p in self.SKIP_PATHS)

    def _url_prefix_lang(self, path):
        """Возвращает 'ru' или 'en' если URL начинается с /ru/ или /en/, иначе None."""
        for lang in self.NON_DEFAULT_LANGS:
            if path == f'/{lang}' or path.startswith(f'/{lang}/'):
                return lang
        return None

    def _detect_browser_lang(self, request):
        """Возвращает 'uz' / 'ru' / 'en' на основе Accept-Language. None если не определить."""
        accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if not accept:
            return None
        for lang_code, _ in parse_accept_lang_header(accept):
            if lang_code == '*':
                break
            try:
                supported = get_supported_language_variant(lang_code).split('-')[0]
            except LookupError:
                continue
            if supported in ('uz', 'ru', 'en'):
                return supported
        return None

    def _set_lang_cookie(self, response, lang):
        response.set_cookie(
            key=settings.LANGUAGE_COOKIE_NAME,
            value=lang,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )

    def _redirect_to_lang(self, request, lang):
        target = f'/{lang}{request.path}'
        qs = request.META.get('QUERY_STRING', '')
        if qs:
            target += f'?{qs}'
        return HttpResponseRedirect(target)

    def _strip_lang_prefix(self, path):
        """Убирает /ru/ или /en/ префикс если есть. Возвращает путь без префикса."""
        for lang in self.NON_DEFAULT_LANGS:
            if path.startswith(f'/{lang}/'):
                return path[len(f'/{lang}'):]
            if path == f'/{lang}':
                return '/'
        return path

    def _build_url_for_lang(self, request, target_lang):
        """Строит URL для целевого языка из текущего пути (заменяя/убирая префикс)."""
        clean_path = self._strip_lang_prefix(request.path)
        if target_lang == 'uz':
            new_path = clean_path
        else:
            new_path = f'/{target_lang}{clean_path}' if clean_path != '/' else f'/{target_lang}/'
        qs = request.META.get('QUERY_STRING', '')
        return new_path + (f'?{qs}' if qs else '')

    def __call__(self, request):
        """Простая и предсказуемая логика без race condition'ов:

        1) Первый заход на `/` без cookie → auto-detect по Accept-Language → редирект.
        2) Заход на URL с префиксом (/ru/..., /en/...) → синхронизируем cookie.
        3) Всё остальное → URL диктует язык, никаких редиректов.

        Это избавляет от проблем с back/forward button (нет агрессивных
        cookie-based редиректов на каждом запросе).
        """
        try:
            if self._should_skip(request) or self._is_bot(request):
                return self.get_response(request)

            cookie_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
            url_lang = self._url_prefix_lang(request.path)

            # === Кейс 1: первый заход на главную без cookie — auto-detect ===
            if request.path == '/' and not cookie_lang:
                detected = self._detect_browser_lang(request)
                if detected in self.NON_DEFAULT_LANGS:
                    response = self._redirect_to_lang(request, detected)
                    self._set_lang_cookie(response, detected)
                    return response
                # Дефолтный язык — остаёмся на /, ставим cookie
                response = self.get_response(request)
                self._set_lang_cookie(response, settings.LANGUAGE_CODE)
                return response

            # === Кейс 2: URL с префиксом — синхронизируем cookie ===
            if url_lang and cookie_lang != url_lang:
                response = self.get_response(request)
                self._set_lang_cookie(response, url_lang)
                return response

            # === Кейс 3: URL без префикса и cookie ещё нет — ставим UZ ===
            if not url_lang and not cookie_lang:
                response = self.get_response(request)
                self._set_lang_cookie(response, settings.LANGUAGE_CODE)
                return response

            # === Кейс 4: всё совпадает — просто пропускаем ===
            return self.get_response(request)

        except Exception as e:
            logger.error(f"Ошибка в AutoLanguageMiddleware: {e}", exc_info=True)
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