"""
Django settings for myproject project.
"""

from pathlib import Path
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')

# ============ ПРИЛОЖЕНИЯ ============

INSTALLED_APPS = [
    'modeltranslation',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ckeditor',
    
    # Third party
    'rest_framework',
    'drf_spectacular',
    'nested_admin',
    'django_filters',
    'corsheaders',
    'reversion',
    
    # Приложения проектов
    'main',  # FAW Uzbekistan
    'kg',    # FAW Kyrgyzstan
]

# ============ REST FRAMEWORK ============

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

LANGUAGE_CODE = 'uz'

USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('uz', "O'zbek"),
    ('ru', 'Русский'),
    ('en', 'English'),
    ('ky', 'Кыргызский'),
]

MODELTRANSLATION_DEFAULT_LANGUAGE = 'uz' 
MODELTRANSLATION_LANGUAGES = ('uz', 'ru', 'en')
MODELTRANSLATION_FALLBACK_LANGUAGES = {
    'default': (),
}

USE_THOUSAND_SEPARATOR = True
NUMBER_GROUPING = 3

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
    "language_chooser": False,
    "show_language_switcher": False,
    
    "topmenu_links": [
        {"name": "Сайт UZ", "url": "https://new.faw.uz", "new_window": True},
        {"name": "Сайт KG", "url": "https://faw.kg", "new_window": True},
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
        "kg.KGHeroSlide": "fas fa-images",
        "kg.IconTemplate": "fas fa-icons",
    },
    
    "order_with_respect_to": [
        "main",
        "kg",
        "auth",
    ],
    
    "custom_links": {
        "main": [{
            "name": "FAW Узбекистан",
            "url": "https://faw.uz",
            "icon": "fas fa-flag",
            "new_window": True
        }],
        "kg": [{
            "name": "FAW Кыргызстан", 
            "url": "https://faw.kg",
            "icon": "fas fa-mountain",
            "new_window": True
        }]
    },
    
    "hide_models": [],
    "usermenu_links": [
        {"model": "auth.user"}
    ],
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
#'myproject.middleware.ForceRussianMiddleware',  # Removed to prevent forcing Russian; re-enable if needed for specific conditions
'corsheaders.middleware.CorsMiddleware',
'django.middleware.common.CommonMiddleware',
'django.middleware.csrf.CsrfViewMiddleware',
'django.contrib.auth.middleware.AuthenticationMiddleware',
'myproject.middleware.RefreshUserPermissionsMiddleware',
'django.contrib.messages.middleware.MessageMiddleware',
'django.middleware.clickjacking.XFrameOptionsMiddleware',
'reversion.middleware.RevisionMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

# ============ TEMPLATES ============

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  
            BASE_DIR / 'main' / 'templates',
            BASE_DIR / 'kg' / 'templates',
        ],
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

# ============ DATABASE ============

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

# ============ ВАЛИДАЦИЯ ПАРОЛЕЙ ============

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============ ЛОКАЛИЗАЦИЯ ============

TIME_ZONE = config('TIME_ZONE', default='Asia/Tashkent')

# ============ СТАТИЧЕСКИЕ ФАЙЛЫ ============

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'main' / 'static',
    BASE_DIR / 'kg' / 'static',   
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============ БЕЗОПАСНОСТЬ ============

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://faw.uz',
    'https://www.faw.uz',
    'https://faw.kg',
    'https://www.faw.kg',
    'https://new.faw.uz',
    'https://www.new.faw.uz',
]

CORS_ALLOWED_ORIGINS = [
    'https://faw.uz',
    'https://www.faw.uz',
    'https://faw.kg',
    'https://www.faw.kg',
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:8080',
    'https://new.faw.uz',
    'https://www.new.faw.uz',
]

CORS_ALLOW_ALL_ORIGINS = DEBUG

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# ============ ПРОДАКШЕН НАСТРОЙКИ ============

if not DEBUG:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        'https://faw.uz',
        'https://www.faw.uz',
        'https://faw.kg', 
        'https://www.faw.kg',
        'https://new.faw.uz',
        'https://www.new.faw.uz',
    ]
    ALLOWED_HOSTS = [
        'new.faw.uz',
        'www.new.faw.uz',
        'faw.uz', 'www.faw.uz',
        'faw.kg', 'www.faw.kg',
        'api.faw.uz', 'api.faw.kg'
    ]
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ============ ЯЗЫКОВЫЕ COOKIES ============

LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_COOKIE_AGE = 365 * 24 * 60 * 60
LANGUAGE_COOKIE_PATH = '/'
LANGUAGE_COOKIE_DOMAIN = None
LANGUAGE_COOKIE_SECURE = not DEBUG
LANGUAGE_COOKIE_HTTPONLY = False
LANGUAGE_COOKIE_SAMESITE = 'Lax'

# ============ CKEDITOR ============

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source']
        ],
        'height': 300,
        'width': '100%',
        'removePlugins': 'elementspath',
        'resize_enabled': False,
        'forcePasteAsPlainText': False,
        'allowedContent': True,
        'extraAllowedContent': 'ul li ol strong p',
    },
}

CKEDITOR_UPLOAD_PATH = "uploads/"

# ============ ЛОГИРОВАНИЕ ============

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'ERROR', 
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
  
        'amocrm_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'amocrm.log', 
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',  
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
     
        'amocrm': {
            'handlers': ['amocrm_file', 'console'],  
            'level': 'INFO',  
            'propagate': False,
        },
    },
}

# Создать директорию для логов
os.makedirs(BASE_DIR / 'logs', exist_ok=True)


SILENCED_SYSTEM_CHECKS = ['ckeditor.W001']

# ========== amoCRM настройки ==========
AMOCRM_SUBDOMAIN = config('AMOCRM_SUBDOMAIN', default='fawtrucks')
AMOCRM_CLIENT_ID = config('AMOCRM_CLIENT_ID')
AMOCRM_CLIENT_SECRET = config('AMOCRM_CLIENT_SECRET')
AMOCRM_REDIRECT_URI = config('AMOCRM_REDIRECT_URI', default='https://new.faw.uz')

AMOCRM_PIPELINE_ID = config('AMOCRM_PIPELINE_ID', default='5811904', cast=int)
AMOCRM_STATUS_ID = config('AMOCRM_STATUS_ID', default='75769098', cast=int)

# ID кастомных полей
AMOCRM_FIELD_REGION = config('AMOCRM_FIELD_REGION', default='3027829', cast=int)
AMOCRM_FIELD_PRODUCT = config('AMOCRM_FIELD_PRODUCT', default='2194355', cast=int)
AMOCRM_FIELD_FORMNAME = config('AMOCRM_FIELD_FORMNAME', default='2194359', cast=int)
AMOCRM_FIELD_FORMID = config('AMOCRM_FIELD_FORMID', default='2194361', cast=int)
AMOCRM_FIELD_REFERER = config('AMOCRM_FIELD_REFERER', default='3022633', cast=int)
AMOCRM_FIELD_UTM = config('AMOCRM_FIELD_UTM', default='3024889', cast=int)
AMOCRM_FIELD_MESSAGE = config('AMOCRM_FIELD_MESSAGE', default='2944145', cast=int)
