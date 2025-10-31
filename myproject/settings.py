"""
Django settings for myproject project.
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')

# Application definition
INSTALLED_APPS = [
    'modeltranslation',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'drf_spectacular',
    'nested_admin',
    'django_filters',
    'corsheaders',
    
    'main',
    'kg',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ============ ЯЗЫКОВЫЕ НАСТРОЙКИ ============

# ЯЗЫК АДМИНКИ (только для Django Admin)
LANGUAGE_CODE = 'ru'  # ← Админка полностью на русском

# Включить поддержку переводов
USE_I18N = True
USE_L10N = True

# Доступные языки для ФРОНТЕНДА
LANGUAGES = [
    ('ru', 'Русский'),
    ('uz', "O'zbek"),
    ('en', 'English'),
    ('ky', 'Кыргызский'),
]

# Настройки ModelTranslation (ТОЛЬКО для контента моделей, НЕ для админки)
MODELTRANSLATION_DEFAULT_LANGUAGE = 'uz'  # Язык по умолчанию для фронтенда
MODELTRANSLATION_LANGUAGES = ('uz', 'ru', 'en')  # Порядок важен!
MODELTRANSLATION_FALLBACK_LANGUAGES = {
    'default': (),
}

# Папка с переводами Django
LOCALE_PATHS = [BASE_DIR / 'locale']

# ============ JAZZMIN НАСТРОЙКИ ============

JAZZMIN_SETTINGS = {
    "site_header": "FAW Admin",
    "site_brand": "VUM",
    "site_logo": "images/logo-vum.png",
    "welcome_sign": "Добро пожаловать в админку VUM",
    "search_model": ["auth.User"],
    "copyright": "VUM",
    "show_sidebar": True,
    "navigation_expanded": False,
    "show_ui_builder": False,
    "custom_css": "css/custom_admin.css",
    

    
    # Принудительно установить русский язык для админки
    "language_chooser": False,  # Отключить выбор языка в админке
    
    "topmenu_links": [
        {"name": "Сайт", "url": "home", "new_window": True},
    ],
    
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        
        "main": "fas fa-globe",
        "main.News": "fas fa-newspaper",
        "main.Product": "fas fa-truck",
        "main.FeatureIcon": "fas fa-icons",
        "main.BecomeADealerPage": "fas fa-file-contract",
        "main.ContactForm": "fas fa-envelope",
        "main.BecomeADealerApplication": "fas fa-handshake",
        "main.Vacancy": "fas fa-briefcase",
        "main.JobApplication": "fas fa-file-pdf",
        "main.Dealer": "fas fa-store",
        "main.DealerService": "fas fa-cogs",
        
        "kg": "fas fa-mountain",
        "kg.KGVehicle": "fas fa-truck",
        "kg.KGFeedback": "fas fa-comment-dots",
    },
    
    "order_with_respect_to": [
        "main",
        "kg",
        "auth",
    ],
    
    "custom_links": {},
    "hide_models": [],
    
    "usermenu_links": [
        {"model": "auth.user"}
    ],
    
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-dark",
    "sidebar": "sidebar-dark-primary",
    "brand_small_text": False,
}

# ============ MIDDLEWARE ============

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # ← Это для фронтенда
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'kg' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n', 
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'main/static'),
    os.path.join(BASE_DIR, 'kg/static'),   
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://127.0.0.1',
    'http://localhost',
]

CORS_ALLOWED_ORIGINS = [
    'https://faw.kg',
    'https://faw.uz',
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:8080',
]

CORS_ALLOW_ALL_ORIGINS = True  # Только для разработки

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

if not DEBUG:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = ['https://faw.kg', 'https://www.faw.kg']
    ALLOWED_HOSTS = ['faw.kg', 'www.faw.kg', 'api.faw.kg']
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Настройки языковых cookies (для фронтенда)
LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_COOKIE_AGE = 365 * 24 * 60 * 60  # 1 год
LANGUAGE_COOKIE_PATH = '/'
LANGUAGE_COOKIE_DOMAIN = None
LANGUAGE_COOKIE_SECURE = False  # True в продакшене
LANGUAGE_COOKIE_HTTPONLY = False
LANGUAGE_COOKIE_SAMESITE = 'Lax'