# Языки и SEO — что исправлено

Документация по работе над:
1. Багом переключения языка (язык сбрасывался при навигации между страницами)
2. Улучшениями SEO (canonical, hreflang, Open Graph, sitemap)

---

## Оглавление

1. [Баг переключения языка — что было сломано](#1-баг-переключения-языка--что-было-сломано)
2. [Найденные причины (их было 5)](#2-найденные-причины-их-было-5)
3. [Что сделано для фикса языка](#3-что-сделано-для-фикса-языка)
4. [Автоопределение языка пользователя](#4-автоопределение-языка-пользователя)
5. [SEO: canonical / hreflang](#5-seo-canonical--hreflang)
6. [SEO: Open Graph](#6-seo-open-graph)
7. [SEO: sitemap.xml](#7-seo-sitemapxml)
8. [Сводка изменённых файлов](#8-сводка-изменённых-файлов)
9. [Что осталось / на будущее](#9-что-осталось--на-будущее)

---

## 1. Баг переключения языка — что было сломано

**Симптомы:**
- На главной (`/`) кликаешь "RU" → переключается на `/ru/`, всё хорошо
- Кликаешь любую внутреннюю ссылку → язык **сбрасывается обратно на UZ**
- При попытке вернуться с RU/EN на UZ — **редирект на тот же URL**, язык не меняется
- Cookie постоянно перезаписывалась

**Где это било:** на каждом клике юзера. Сайт фактически работал только на одном языке — узбекском.

---

## 2. Найденные причины (их было 5)

Это был не один баг, а **цепочка из 5 независимых проблем**:

### 2.1 Дубль `main.urls` в [myproject/urls.py](myproject/urls.py)

`main.urls` подключался дважды: один раз **без** префикса языка, второй раз **через** `i18n_patterns`. Django при генерации `{% url 'home' %}` находил первый paттерн → возвращал URL **без** префикса. Все ссылки в шаблонах вели на `/about/`, никогда на `/ru/about/`.

### 2.2 Меню берёт URL из БД ([NavItem.url](main/models.py))

Ссылки в шапке/футере рендерились как `{{ item.url }}` — это сохранённый в БД путь типа `/about/` без префикса. Даже после фикса 2.1 — навигация всё равно вела на UZ-версии.

### 2.3 `ForceRussianMiddleware` форсил UZ для всего фронта

Кастомный middleware смотрел **только** на URL-префикс, **игнорируя** cookie и сессию. Если URL не начинался с `/ru/` или `/en/` — принудительно ставил UZ.

### 2.4 `LanguageCookieMiddleware` перезатирал cookie

Этот middleware шёл **после** `set_language` view. Он сравнивал текущий активный язык (UZ — из-за бага 2.3) с cookie которую только что поставил `set_language` (например `ru`), видел расхождение → **переписывал cookie обратно на `uz`**. Из-за этого язык менялся "один раз" — первый клик ставил cookie, но любой следующий клик возвращал её обратно.

### 2.5 `LocaleMiddleware` Django сам игнорирует cookie при `prefix_default_language=False`

Это **сознательное поведение Django 5.1** (а не баг). Когда используется `i18n_patterns(prefix_default_language=False)` и URL **без** префикса (например `/set-language/`) — Django **всегда** активирует дефолтный язык (UZ), игнорируя cookie. Это сделано чтобы избежать неоднозначности: URL `/about/` всегда показывает UZ-контент, никогда RU.

Из-за этого внутри view `set_language` функция `translate_url('/ru/about/', 'uz')` вызывалась в **UZ-контексте**. Она пыталась `resolve('/ru/about/')` и получала **404** (`/ru/...` URL не существует в UZ-патернах). Без успешного `resolve` функция возвращала URL **без изменений** → редирект шёл на тот же `/ru/about/` → язык не переключался.

---

## 3. Что сделано для фикса языка

### 3.1 Убран дубль `main.urls`
[myproject/urls.py](myproject/urls.py) — оставлено **только** подключение через `i18n_patterns`:
```python
urlpatterns += i18n_patterns(
    path('', include('main.urls')),
    prefix_default_language=False,
)
```
Теперь `{% url 'home' %}` возвращает:
- `/` в UZ-контексте
- `/ru/` в RU-контексте
- `/en/` в EN-контексте

### 3.2 Создан template-фильтр `with_lang_prefix`
[main/templatetags/seo_tags.py](main/templatetags/seo_tags.py) — фильтр который добавляет языковой префикс к URL из БД:

```django
<a href="{{ item.url|with_lang_prefix:LANGUAGE_CODE }}">
```

Логика:
- Внешние ссылки (`http://`, `mailto:`, `tel:`) — не трогаются
- Если URL уже имеет префикс — снимается и пересобирается под нужный язык
- Для UZ (дефолт) — префикс не добавляется
- Для RU/EN — добавляется

Применён в [header.html](main/templates/main/includes/header.html) (6 ссылок) и [footer.html](main/templates/main/includes/footer.html) (1 ссылка).

### 3.3 `ForceRussianMiddleware` упрощён
[myproject/middleware.py](myproject/middleware.py) — теперь обрабатывает **только**:
- `/admin/` — принудительно RU (админка одноязычная)
- `/api/uz|ru|en|kg/` — язык по URL-префиксу
- Для всех остальных страниц **ничего не делает** — этим занимается стандартный `LocaleMiddleware`

### 3.4 `LanguageCookieMiddleware` полностью удалён
Его задача (запоминать язык в cookie при переходе по URL с префиксом) теперь решается стандартным Django-механизмом через `set_language` view.

### 3.5 Своя обёртка над `set_language`
[myproject/urls.py](myproject/urls.py) — добавлена функция-обёртка которая **активирует язык на основе `next_url`** ПЕРЕД вызовом стандартного Django view:

```python
def set_language(request):
    if request.method == 'POST':
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '/')
        parts = next_url.lstrip('/').split('/', 1)
        if parts and parts[0] in supported_languages:
            translation.activate(parts[0])  # ← КЛЮЧЕВАЯ СТРОКА
    return django_set_language(request)
```

Это компенсирует особенность Django 5.1 (баг 2.5) — теперь `translate_url` внутри стандартного view корректно резолвит `/ru/about/` потому что RU активирован.

### 3.6 Удалён неиспользуемый код
Старая функция `set_language_get` в [main/views.py](main/views.py) удалена — её заменил стандартный Django view + наша обёртка.

### Результат

Все 5 кейсов переключения работают (проверено автотестом):

| Сценарий | Результат |
|----------|-----------|
| UZ `/` → RU | `/ru/` ✓ |
| RU `/ru/` → UZ | `/` ✓ |
| RU `/ru/about/` → UZ | `/about/` ✓ |
| RU `/ru/about/` → EN | `/en/about/` ✓ |
| EN `/en/products/` → UZ | `/products/` ✓ |

---

## 4. Автоопределение языка пользователя

### 4.1 Что было

Юзер из России открывает `https://faw.uz/` — браузер шлёт `Accept-Language: ru-RU,ru;q=0.9`. Но Django **игнорирует** этот заголовок при `prefix_default_language=False` для URL без префикса (см. баг 2.5). Юзер видит UZ-сайт, хотя у него настройки русские.

### 4.2 Что сделано — `AutoLanguageMiddleware`

Новый middleware в [myproject/middleware.py](myproject/middleware.py), подключён в `MIDDLEWARE` **до** `LocaleMiddleware`.

**Логика работы:**

#### A. URL **без** префикса (`/`, `/about/`, `/contact/`):

| Условие | Действие |
|---------|----------|
| `cookie = ru` или `cookie = en` | Редирект на `/<lang>/<path>` |
| `cookie = uz` | Остаёмся (юзер явно выбрал UZ) |
| Cookie нет, Accept-Language → ru/en | Редирект + ставим cookie |
| Cookie нет, Accept-Language → uz/непонятно | Остаёмся UZ, cookie не ставим |

#### B. URL **с** префиксом (`/ru/...`, `/en/...`):

- Если cookie отличается от URL-префикса → **обновляем cookie** под текущий язык
- Так юзер открывший `/ru/about/` из закладки получит `/ru/` при последующем заходе на `/`

#### C. Пропускаем (никаких манипуляций):

- Не-GET запросы (POST/PUT — формы, AJAX)
- Боты (User-Agent содержит `bot`, `crawler`, `googlebot`, `yandex`, `facebookexternalhit` и т.д.)
- Служебные URL: `/admin/`, `/api/`, `/set-language/`, `/sitemap*`, `/robots.txt`, `/media/`, `/static/`, `/dealer/`, `/nested_admin/`
- Невалидный `/uz/` префикс (в нашей схеме `prefix_default_language=False`)

### 4.3 Сценарии которые работают

Проверены автотестом, все 8 кейсов:

| Сценарий | Результат |
|----------|-----------|
| RU-юзер открыл `/` первый раз | → `/ru/` + cookie=ru |
| RU-юзер открыл `/about/` напрямую | → `/ru/about/` + cookie=ru |
| Кто-то скинул `/ru/products/` | Открывается + cookie=ru ставится |
| Cookie=uz, открывает `/about/` | Остаётся UZ |
| UZ-юзер (Accept-Language=uz), нет cookie | Остаётся UZ, cookie не ставим |
| Googlebot открыл `/` (Accept-Language=ru) | Не редиректнули — индексирует UZ |
| EN-юзер открыл `/products/?category=samosval` | → `/en/products/?category=samosval` + cookie=en (query сохранился) |
| Cookie=ru + Accept-Language=uz | Cookie приоритет → `/ru/` |

### 4.4 Почему именно так

**Cookie приоритет над Accept-Language:** Юзер уже сделал явный выбор когда-то — мы его уважаем. Если кто-то системно поставил себе русский, но потом руками выбрал на сайте узбекский — каждый следующий заход не редиректит обратно.

**Боты пропускаются:** Если редиректить Googlebot — он проиндексирует UZ-главную как RU/EN. Это **сломает SEO**. Нужно чтобы каждая языковая версия индексировалась под своим URL.

**Cookie не ставим при определении UZ:** Намеренно. Юзер ещё не сделал выбор — будем продолжать определять при каждом заходе. Если потом он явно выберет — cookie встанет.

**Query-параметры сохраняются:** При редиректе с `/products/?category=samosval` мы добавляем `?category=samosval` к новому URL.

---

## 5. SEO: canonical / hreflang

### 4.1 Что было сломано

**Canonical:**
- Зависел от `Host` заголовка → разные URL для `www.faw.uz`, `faw.uz`, IP → Google делил SEO-вес
- Для категорий каталога (`/products/?category=samosval`) возвращался **пустой** тег → Google не знал какой URL индексировать как канонический
- Включал tracking-параметры (UTM, fbclid) → ложные дубли в индексе

**Hreflang:**
- Тоже зависел от `Host`
- Тоже включал tracking-параметры → дубли × N языков

### 4.2 Что сделано

[main/templatetags/seo_tags.py](main/templatetags/seo_tags.py):

**Добавлены хелперы:**
- `TRACKING_PARAMS` — список из 13 трекинговых параметров (`utm_*`, `fbclid`, `gclid`, `yclid`, `msclkid`, `ym_*`, `_ga`, `_gl`)
- `_clean_query_string(qs)` — убирает tracking-параметры, оставляет контентные (например `?category=samosval`)
- `_canonical_base(request)` — возвращает `https://faw.uz` в проде, `request.get_host()` в DEBUG

**Переписаны теги:**
- `canonical_url` — теперь **всегда** возвращает тег (никаких пустых строк), хардкод домена, UTM убираются
- `hreflang_tags` — то же самое, плюс UTM убираются из всех языковых URL

### 4.3 Что это даёт

| Сценарий | Было | Стало |
|----------|------|-------|
| `/about/?utm_source=google` | canonical = `/about/?utm_source=google` | canonical = `/about/` |
| `/products/?category=samosval` | canonical отсутствовал | canonical = `/products/?category=samosval` |
| Категория + UTM | canonical с обоими параметрами | canonical = `/products/?category=samosval` |
| Заход через `www.faw.uz` | canonical с www | canonical = `https://faw.uz/...` |

**Что НЕ изменилось** (важно):
- UTM-метки **остаются в URL** в адресной строке браузера
- Аналитика (GTM, Yandex Metrika, FB Pixel) **продолжает работать**
- AmoCRM по-прежнему получает UTM при отправке форм
- Дашборд считает поток как считал — мы убираем UTM только из **информационных тегов для поисковиков**

### 4.4 Важное про hreflang

Сейчас работает для статичных страниц (about, contact и т.д.) и для динамики со **стабильными slug'ами** (одинаковый slug на всех языках). Если в будущем slug новости/продукта будет переводиться (через django-modeltranslation) — потребуется доработка генератора hreflang.

---

## 6. SEO: Open Graph

### 5.1 Что было сломано

В [seo_meta.html](main/templates/main/includes/seo_meta.html) при наличии `PageMeta` рендерились `og:title`, `og:description`, `og:type`, `og:site_name`, `og:url`, `og:image`. Но **не было**:

- `og:locale` — какой язык страницы
- `og:locale:alternate` — какие альтернативные языки есть

Без этих тегов Facebook/LinkedIn:
- Не знали что у страницы есть переводы
- Не могли показать превью на языке юзера соцсети

**Дополнительно:** fallback (когда `PageMeta` нет) был **хардкод на русском** для всех языков и **не содержал og:* тегов вообще**.

### 5.2 Что сделано

**Добавлены `og:locale` теги** для всех трёх языков:
```html
<!-- На UZ-странице -->
<meta property="og:locale" content="uz_UZ">
<meta property="og:locale:alternate" content="ru_RU">
<meta property="og:locale:alternate" content="en_US">
```

**Локализован fallback** — три варианта (UZ / RU / EN) с полным набором тегов: `<title>`, `<meta description>`, `<meta keywords>`, `og:title`, `og:description`, `og:type`, `og:site_name`, `og:url`.

### 5.3 Что это даёт

Когда кто-то делится ссылкой на FAW в Facebook/LinkedIn/Telegram/WhatsApp:
- Соцсеть знает на каком языке страница
- Если у юзера в FB настроен русский интерфейс, а друг скинул UZ-ссылку — Facebook **сам подтянет** превью с `/ru/...` версии
- Юзер видит превью на **своём** языке → выше CTR (click-through rate)

**Контентная задача (на проде):** в админке для каждой страницы должна быть заполнена `PageMeta` со всеми тремя языками (`title_uz/ru/en`, `description_uz/ru/en` и т.д.). На проде это уже сделано.

---

## 7. SEO: sitemap.xml

### 6.1 Что было сломано

1. **URL'ы зависели от `Host` заголовка** — sitemap, запрошенный через www, выдавал URL с www
2. **`protocol = 'https'` хардкод** даже в DEBUG → локально показывался `https://localhost` (невалидный URL)
3. **`lastmod = datetime.now()`** для статичных страниц → каждый запрос Google видел свежую дату → думал "страница часто меняется, нужна переиндексация" → лишний расход crawl budget

### 6.2 Что сделано

[main/views_sitemap.py](main/views_sitemap.py) — добавлен хелпер `_sitemap_base(request)`:
- Прод → `https://faw.uz` (хардкод, не зависит от Host)
- DEBUG → `request.get_host()` (удобство локалки)

[main/sitemaps.py](main/sitemaps.py):
- `protocol = 'http' if settings.DEBUG else 'https'` — динамический
- Константа `STATIC_PAGES_LASTMOD = datetime(2026, 1, 1, ...)` — статичная дата для статических страниц
- Категории каталога fallback теперь использует `STATIC_PAGES_LASTMOD` вместо `datetime.now()`

### 6.3 Что это даёт

- Sitemap на проде всегда указывает на `https://faw.uz/...` независимо от Host
- Google перестанет тратить crawl budget на постоянную переиндексацию статики
- В локалке sitemap выдаёт читаемые `http://localhost/...` URL

**Обновление даты:** при значимом редизайне или обновлении контента статических страниц меняй константу `STATIC_PAGES_LASTMOD` в [sitemaps.py](main/sitemaps.py).

---

## 8. Сводка изменённых файлов

| Файл | Изменения |
|------|-----------|
| [myproject/urls.py](myproject/urls.py) | Убран дубль `include('main.urls')`. Добавлена обёртка `set_language` с активацией языка по next_url. |
| [myproject/middleware.py](myproject/middleware.py) | `ForceRussianMiddleware` упрощён до admin/api. `LanguageCookieMiddleware` удалён. Добавлен `AutoLanguageMiddleware` (авто-детекция языка по Accept-Language + синхронизация cookie). |
| [myproject/settings.py](myproject/settings.py) | `LanguageCookieMiddleware` убран из `MIDDLEWARE`. Добавлен `AutoLanguageMiddleware` перед `LocaleMiddleware`. |
| [main/views.py](main/views.py) | Удалена неиспользуемая `set_language_get`. |
| [main/templatetags/seo_tags.py](main/templatetags/seo_tags.py) | Новый фильтр `with_lang_prefix`. Хелперы `TRACKING_PARAMS`, `_clean_query_string`, `_canonical_base`. Переписаны `canonical_url` и `hreflang_tags`. |
| [main/templates/main/includes/header.html](main/templates/main/includes/header.html) | Все `{{ item.url }}` / `{{ child.url }}` обёрнуты в фильтр `with_lang_prefix`. |
| [main/templates/main/includes/footer.html](main/templates/main/includes/footer.html) | То же для `nav_footer`. |
| [main/templates/main/includes/seo_meta.html](main/templates/main/includes/seo_meta.html) | Добавлены `og:locale` + `og:locale:alternate`. Fallback локализован на 3 языка с полным набором og:* тегов. |
| [main/views_sitemap.py](main/views_sitemap.py) | Хелпер `_sitemap_base()`. Хардкод домена в проде. |
| [main/sitemaps.py](main/sitemaps.py) | Динамический `protocol` по DEBUG. Константа `STATIC_PAGES_LASTMOD`. |

---

## 9. Что осталось / на будущее

| Задача | Приоритет | Сложность |
|--------|-----------|-----------|
| Дефолтный `og:image` в fallback | 🟢 Низкий | 5 минут |
| Slug-проверка для hreflang динамики | 🟡 Средний (если slug'и будут переводиться) | 30 минут |
| `xhtml:link` hreflang в sitemap | 🟢 Низкий (есть HTML-hreflang) | 1 час |
| Структурные URL для категорий (`/products/category/samosval/` вместо `?category=`) | 🟡 Средний (улучшит CTR в выдаче) | 3-4 часа + миграция |
| Заполнить `PageMeta` для всех страниц на проде | 🔴 Высокий (если не заполнено) | Контент-задача |

---

## Кратко о философии решения

1. **Меньше своего кода, больше Django-built-in** — заменили `set_language_get` на встроенный Django view, удалили `LanguageCookieMiddleware`, упростили `ForceRussianMiddleware`. Django auth/locale протестированы миллионами проектов.
2. **Defense in depth для SEO** — canonical + hreflang + og:locale + sitemap работают вместе. Если один из источников не сработает (например, FB не прочитал sitemap) — другой компенсирует.
3. **Хардкод домена в проде, динамика в DEBUG** — единый паттерн для canonical, hreflang, og:url и sitemap. Это гарантирует что Google видит **один** канонический домен.
4. **Tracking-параметры не удаляем из URL** — только из информационных тегов. Аналитика и трекинг продолжают работать.

---

_Последнее обновление: июнь 2026_
