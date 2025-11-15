# 🚀 FAW SITE Backend

Backend проект на **Django + Django REST Framework** для сайтов:
- 🇺🇿 **FAW.UZ** (Узбекистан)
- 🇰🇬 **FAW.KG** (Кыргызстан)

Проект включает админ-панель, REST API, Swagger-документацию и мультиязычную поддержку.


---

## 🧩 Стек технологий

- **Python 3.13**
- **Django 5.2.7**
- **Django REST Framework 3.16.1**
- **PostgreSQL** (БД)
- **drf-spectacular** — автогенерация Swagger / OpenAPI документации
- **django-jazzmin** — современная админка
- **django-modeltranslation** — мультиязычность моделей
- **Pillow** — работа с изображениями
- **psycopg2-binary** — драйвер PostgreSQL
- **python-decouple** — управление env-переменными

##  pip list
##  Package                   Version
##  ------------------------- ---------
##  asgiref                   3.9.2
##  attrs                     25.3.0
##  blinker                   1.9.0
##  click                     8.3.0
##  colorama                  0.4.6
##  Django                    5.2.6
##  django-jazzmin            3.0.1
##  djangorestframework       3.16.1
##  drf-spectacular           0.28.0
##  drf-spectacular-sidecar   2025.10.1
##  Flask                     3.1.2
##  Flask-SQLAlchemy          3.1.1
##  greenlet                  3.2.4
##  importlib_resources       6.5.2
##  inflection                0.5.1
##  itsdangerous              2.2.0
##  Jinja2                    3.1.6
##  jsonschema                4.25.1
##  jsonschema-specifications 2025.9.1
##  MarkupSafe                3.0.3
##  packaging                 25.0
##  pillow                    11.3.0
##  pip                       25.2
##  psycopg2-binary           2.9.10
##  python-decouple           3.8
##  pytz                      2025.2
##  PyYAML                    6.0.3
##  referencing               0.36.2
##  rpds-py                   0.27.1
##  SQLAlchemy                2.0.43
##  sqlparse                  0.5.3
##  swagger-spec-validator    3.0.4
##  typing_extensions         4.15.0
##  tzdata                    2025.2
##  uritemplate               4.2.0
##  Werkzeug                  3.1.3
##  django-modeltranslation   0.19.17


## ⚙️ Установка и запуск проекта

### 1️⃣ Клонировать репозиторий
```bash
git clone https://github.com/your-username/FAW_SITE-back.git
cd FAW_SITE-back/myproject
2️⃣ Создать и активировать виртуальное окружение
Windows:

bash
Копировать код
python -m venv venv
venv\Scripts\activate
macOS / Linux:

bash
Копировать код
python3 -m venv venv
source venv/bin/activate
3️⃣ Установить зависимости
bash
Копировать код
pip install -r requirements.txt
Если файла requirements.txt нет — создай его этой командой:

bash
Копировать код
pip freeze > requirements.txt
4️⃣ Применить миграции базы данных
bash
Копировать код
### Миграции запуск применение и откат
python manage.py makemigrations
python manage.py migrate
⏪ Откатить миграцию назад на 1 шаг
python manage.py migrate app_name migration_name
Пример:
python manage.py migrate news 0002

🧹 Сбор статических файлов (collectstatic)
Если проект деплоится на сервер и нужны статики:

python manage.py collectstatic

bash
python manage.py save_amocrm_tokens
       "access_token": "НОВЫЙ_ACCESS_TOKEN",
       "refresh_token": "НОВЫЙ_REFRESH_TOKEN"
       
5️⃣ Создать суперпользователя
bash
Копировать код
python manage.py createsuperuser
6️⃣ Запустить сервер
bash
Копировать код
python manage.py runserver
После этого проект будет доступен по адресу:
👉 http://127.0.0.1:8000/

🧠 Полезные URL
Раздел	URL
Админка	http://127.0.0.1:8000/admin/
Новости (HTML)	http://127.0.0.1:8000/news/
API новостей	http://127.0.0.1:8000/api/news/
Swagger UI	http://127.0.0.1:8000/api/docs/
OpenAPI JSON	http://127.0.0.1:8000/api/schema/

🖼️ Работа с медиафайлами
Файлы изображений и видео сохраняются в директории:

bash
Копировать код
/media/news/
Для корректной работы убедись, что в settings.py добавлены:

python
Копировать код
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
🧾 Основные зависимости (requirements.txt)
text
Копировать код
Django>=5.0
djangorestframework
drf-spectacular
Pillow
Если используешь PostgreSQL:

text
Копировать код
psycopg2-binary
🌐 Локализация
Проект поддерживает мультиязычность (/i18n/).
Чтобы сменить язык, можно отправить GET-запрос:

bash
Копировать код
/i18n/setlang/?language=ru
/i18n/setlang/?language=en
🧑‍💻 Автор
FAW Dev Team
📧 support@faw-site.local
📅 2025

💡 Примечания
Проект поддерживает Django Admin с кастомными инлайнами для блоков новостей.

API возвращает новости с их блоками в формате JSON.

Swagger (через drf-spectacular) позволяет тестировать API прямо из браузера.

yaml
Копировать код
