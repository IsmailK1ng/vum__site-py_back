"""
🚀 PRODUCTION HEALTH CHECK
Полная проверка продакшена

Запуск:
python manage.py prod_health_check
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.core.management import call_command
from io import StringIO
import requests
import time


class Command(BaseCommand):
    help = 'Полная проверка production сервера'
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("🚀 PRODUCTION HEALTH CHECK"))
        self.stdout.write("="*70 + "\n")
        
        errors = []
        warnings = []
        
        # Определяем базовый URL
        if not settings.DEBUG:
            # На проде используем реальный домен
            base_url = f"https://{settings.ALLOWED_HOSTS[0]}" if settings.ALLOWED_HOSTS else "http://localhost:8000"
        else:
            # На локалке используем localhost
            base_url = "http://127.0.0.1:8000"
            self.stdout.write(self.style.WARNING(f"⚠️  ЛОКАЛЬНАЯ СРЕДА (DEBUG=True)"))
            self.stdout.write(f"   Базовый URL: {base_url}")
            self.stdout.write(f"   Убедитесь, что сервер запущен: python manage.py runserver\n")
        
        # ==========================================
        # 1. НАСТРОЙКИ DJANGO
        # ==========================================
        
        self.stdout.write(self.style.HTTP_INFO("📋 1. НАСТРОЙКИ DJANGO"))
        self.stdout.write("-" * 70)
        
        # DEBUG
        if settings.DEBUG:
            warnings.append("DEBUG=True (только для локальной разработки)")
            self.stdout.write(self.style.WARNING("⚠️  DEBUG = True (локальная среда)"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ DEBUG = False"))
        
        # SECRET_KEY
        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 50:
            errors.append("SECRET_KEY слишком короткий")
            self.stdout.write(self.style.ERROR("❌ SECRET_KEY проблема"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ SECRET_KEY ({len(settings.SECRET_KEY)} символов)"))
        
        # ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS:
            errors.append("ALLOWED_HOSTS пустой")
            self.stdout.write(self.style.ERROR("❌ ALLOWED_HOSTS не настроен"))
        elif '*' in settings.ALLOWED_HOSTS and not settings.DEBUG:
            errors.append("ALLOWED_HOSTS = ['*'] на проде")
            self.stdout.write(self.style.ERROR("❌ ALLOWED_HOSTS = ['*']"))
        else:
            hosts_display = ', '.join(settings.ALLOWED_HOSTS[:5])
            self.stdout.write(self.style.SUCCESS(f"✅ ALLOWED_HOSTS: {hosts_display}"))
        
        # SECURE COOKIES
        if not settings.DEBUG:
            if not settings.SESSION_COOKIE_SECURE:
                errors.append("SESSION_COOKIE_SECURE=False на проде")
                self.stdout.write(self.style.ERROR("❌ SESSION_COOKIE_SECURE = False"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ SESSION_COOKIE_SECURE = True"))
            
            if not settings.CSRF_COOKIE_SECURE:
                errors.append("CSRF_COOKIE_SECURE=False на проде")
                self.stdout.write(self.style.ERROR("❌ CSRF_COOKIE_SECURE = False"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ CSRF_COOKIE_SECURE = True"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  DEBUG=True, пропускаем проверку secure cookies"))
        
        # TIMEZONE
        expected_tz = 'Asia/Tashkent'
        if settings.TIME_ZONE != expected_tz:
            warnings.append(f"TIME_ZONE = {settings.TIME_ZONE} (ожидалось {expected_tz})")
            self.stdout.write(self.style.WARNING(f"⚠️  TIME_ZONE = {settings.TIME_ZONE}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ TIME_ZONE = {expected_tz}"))
        
        if not settings.USE_TZ:
            errors.append("USE_TZ=False")
            self.stdout.write(self.style.ERROR("❌ USE_TZ = False"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ USE_TZ = True"))
        
        # ==========================================
        # 2. БАЗА ДАННЫХ
        # ==========================================
        
        self.stdout.write(self.style.HTTP_INFO("\n📊 2. БАЗА ДАННЫХ"))
        self.stdout.write("-" * 70)
        
        try:
            with connection.cursor() as cursor:
                # Версия БД
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                db_version = f"{version.split()[0]} {version.split()[1]}"
                self.stdout.write(self.style.SUCCESS(f"✅ Подключение: {db_version}"))
                
                # Продукты
                cursor.execute("SELECT COUNT(*) FROM main_product")
                total_products = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM main_product WHERE is_active=true")
                active_products = cursor.fetchone()[0]
                
                if total_products == 0:
                    errors.append("Нет продуктов в БД")
                    self.stdout.write(self.style.ERROR("❌ Продуктов: 0"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"✅ Продуктов: {total_products} (активных: {active_products})"))
                
                # Новости
                cursor.execute("SELECT COUNT(*) FROM main_news WHERE is_active=true")
                news_count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"✅ Новостей: {news_count}"))
                
                # Дилеры
                cursor.execute("SELECT COUNT(*) FROM main_dealer WHERE is_active=true")
                dealer_count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"✅ Дилеров: {dealer_count}"))
                
                # Заявки
                cursor.execute("SELECT COUNT(*) FROM main_contactform")
                leads_count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"✅ Заявок: {leads_count}"))
                
                # Проверка дубликатов slug
                cursor.execute("""
                    SELECT slug, COUNT(*) as count
                    FROM main_product
                    GROUP BY slug
                    HAVING COUNT(*) > 1
                """)
                dup_products = cursor.fetchall()
                
                if dup_products:
                    errors.append(f"Дубликаты slug у продуктов: {len(dup_products)}")
                    self.stdout.write(self.style.ERROR(f"❌ Дубликаты slug продуктов: {len(dup_products)}"))
                    for slug, count in dup_products[:3]:
                        self.stdout.write(f"   '{slug}' встречается {count} раз")
                else:
                    self.stdout.write(self.style.SUCCESS("✅ Дубликатов slug нет"))
                
                # Проверка дубликатов order в ProductFeature
                cursor.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT product_id, "order", COUNT(*) as count
                        FROM main_productfeature
                        GROUP BY product_id, "order"
                        HAVING COUNT(*) > 1
                    ) AS dup
                """)
                dup_order_count = cursor.fetchone()[0]
                
                if dup_order_count > 0:
                    warnings.append(f"Дубликаты order в ProductFeature: {dup_order_count}")
                    self.stdout.write(self.style.WARNING(f"⚠️  Дубликаты order: {dup_order_count}"))
                else:
                    self.stdout.write(self.style.SUCCESS("✅ Дубликатов order нет"))
                
        except Exception as e:
            errors.append(f"Ошибка БД: {str(e)}")
            self.stdout.write(self.style.ERROR(f"❌ Ошибка БД: {str(e)}"))
        
        # ==========================================
        # 3. СКОРОСТЬ САЙТА (только на проде)
        # ==========================================
        
        if not settings.DEBUG:
            self.stdout.write(self.style.HTTP_INFO("\n⚡ 3. СКОРОСТЬ САЙТА"))
            self.stdout.write("-" * 70)
            
            pages_to_check = {
                '/': 'Главная',
                '/products/': 'Продукты',
                '/contact/': 'Контакты',
                '/api/uz/products/': 'API Продукты',
            }
            
            for url, name in pages_to_check.items():
                try:
                    full_url = f"{base_url}{url}"
                    start = time.time()
                    response = requests.get(full_url, timeout=10, verify=False)
                    duration = (time.time() - start) * 1000
                    
                    if response.status_code != 200:
                        errors.append(f"{name} недоступна (код {response.status_code})")
                        self.stdout.write(self.style.ERROR(f"❌ {name}: {response.status_code}"))
                    elif duration < 100:
                        self.stdout.write(self.style.SUCCESS(f"✅ {name}: {duration:.0f}ms - ОТЛИЧНО"))
                    elif duration < 300:
                        self.stdout.write(self.style.SUCCESS(f"✅ {name}: {duration:.0f}ms - ХОРОШО"))
                    elif duration < 1000:
                        self.stdout.write(self.style.WARNING(f"⚠️  {name}: {duration:.0f}ms - МЕДЛЕННО"))
                        warnings.append(f"{name} медленная ({duration:.0f}ms)")
                    else:
                        self.stdout.write(self.style.ERROR(f"❌ {name}: {duration:.0f}ms - ОЧЕНЬ МЕДЛЕННО"))
                        errors.append(f"{name} слишком медленная ({duration:.0f}ms)")
                except Exception as e:
                    errors.append(f"{name}: {str(e)}")
                    self.stdout.write(self.style.ERROR(f"❌ {name}: {str(e)}"))
            
            # ==========================================
            # 4. ЯЗЫКИ (только на проде)
            # ==========================================
            
            self.stdout.write(self.style.HTTP_INFO("\n🌐 4. МУЛЬТИЯЗЫЧНОСТЬ"))
            self.stdout.write("-" * 70)
            
            languages = ['uz', 'ru', 'en']
            
            for lang in languages:
                try:
                    # Главная
                    response = requests.get(f"{base_url}/", headers={'Accept-Language': lang}, timeout=10, verify=False)
                    if response.status_code != 200:
                        errors.append(f"Главная на {lang} не работает")
                        self.stdout.write(self.style.ERROR(f"❌ {lang.upper()}: Главная не работает"))
                    else:
                        # API
                        api_response = requests.get(f"{base_url}/api/{lang}/products/", timeout=10, verify=False)
                        if api_response.status_code != 200:
                            errors.append(f"API {lang} не работает")
                            self.stdout.write(self.style.ERROR(f"❌ {lang.upper()}: API не работает"))
                        else:
                            self.stdout.write(self.style.SUCCESS(f"✅ {lang.upper()}: Сайт + API работают"))
                except Exception as e:
                    errors.append(f"Язык {lang}: {str(e)}")
                    self.stdout.write(self.style.ERROR(f"❌ {lang.upper()}: {str(e)}"))
        else:
            self.stdout.write(self.style.HTTP_INFO("\n⚡ 3. СКОРОСТЬ САЙТА"))
            self.stdout.write("-" * 70)
            self.stdout.write(self.style.WARNING("⚠️  Пропущено (DEBUG=True)"))
            self.stdout.write("   Запустите на проде для проверки скорости")
            
            self.stdout.write(self.style.HTTP_INFO("\n🌐 4. МУЛЬТИЯЗЫЧНОСТЬ"))
            self.stdout.write("-" * 70)
            self.stdout.write(self.style.WARNING("⚠️  Пропущено (DEBUG=True)"))
            self.stdout.write("   Запустите на проде для проверки языков")
        
        # ==========================================
        # 5. amoCRM
        # ==========================================
        
        self.stdout.write(self.style.HTTP_INFO("\n🔗 5. amoCRM ИНТЕГРАЦИЯ"))
        self.stdout.write("-" * 70)
        
        # Настройки amoCRM
        amocrm_settings = {
            'AMOCRM_SUBDOMAIN': getattr(settings, 'AMOCRM_SUBDOMAIN', None),
            'AMOCRM_CLIENT_ID': getattr(settings, 'AMOCRM_CLIENT_ID', None),
            'AMOCRM_CLIENT_SECRET': getattr(settings, 'AMOCRM_CLIENT_SECRET', None),
            'AMOCRM_PIPELINE_ID': getattr(settings, 'AMOCRM_PIPELINE_ID', None),
            'AMOCRM_STATUS_ID': getattr(settings, 'AMOCRM_STATUS_ID', None),
        }
        
        for key, value in amocrm_settings.items():
            if not value:
                errors.append(f"{key} не установлен")
                self.stdout.write(self.style.ERROR(f"❌ {key} не установлен"))
            else:
                display = str(value)[:30] + '...' if 'SECRET' not in key else '***'
                self.stdout.write(self.style.SUCCESS(f"✅ {key} = {display}"))
        
        # Токен amoCRM в БД
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT access_token, refresh_token, expires_at
                    FROM main_amocrmtoken WHERE id=1
                """)
                token_row = cursor.fetchone()
                
                if not token_row:
                    warnings.append("amoCRM токен не найден в БД")
                    self.stdout.write(self.style.WARNING("⚠️  Токен в БД отсутствует"))
                    self.stdout.write("   Запустите: python manage.py init_amocrm_tokens")
                else:
                    access_token, refresh_token, expires_at = token_row
                    
                    if not access_token or not refresh_token:
                        errors.append("amoCRM токены пустые")
                        self.stdout.write(self.style.ERROR("❌ Токены пустые"))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"✅ Токен: {access_token[:20]}..."))
                        
                        from django.utils import timezone
                        if expires_at < timezone.now():
                            self.stdout.write(self.style.WARNING("⚠️  Токен истёк (обновится автоматически)"))
                        else:
                            self.stdout.write(self.style.SUCCESS(f"✅ Активен до: {expires_at.strftime('%Y-%m-%d %H:%M')}"))
        except Exception as e:
            warnings.append(f"Ошибка проверки токена: {str(e)}")
        
        # ==========================================
        # 6. МИГРАЦИИ
        # ==========================================
        
        self.stdout.write(self.style.HTTP_INFO("\n📦 6. МИГРАЦИИ"))
        self.stdout.write("-" * 70)
        
        try:
            output = StringIO()
            call_command('showmigrations', '--plan', stdout=output)
            migrations_output = output.getvalue()
            
            unapplied = [line for line in migrations_output.split('\n') if '[ ]' in line]
            
            if unapplied:
                errors.append(f"{len(unapplied)} миграций не применены")
                self.stdout.write(self.style.ERROR(f"❌ Не применено: {len(unapplied)}"))
                for migration in unapplied[:5]:
                    self.stdout.write(f"   {migration}")
                self.stdout.write("\n   Запустите: python manage.py migrate")
            else:
                self.stdout.write(self.style.SUCCESS("✅ Все миграции применены"))
        except Exception as e:
            warnings.append(f"Ошибка проверки миграций: {str(e)}")
            self.stdout.write(self.style.WARNING(f"⚠️  {str(e)}"))
        
        # ==========================================
        # ФИНАЛЬНЫЙ ОТЧЁТ
        # ==========================================
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.HTTP_INFO("📊 ФИНАЛЬНЫЙ ОТЧЁТ"))
        self.stdout.write("="*70)
        
        # Фильтруем ошибки для локальной среды
        if settings.DEBUG:
            # На локалке убираем DEBUG из ошибок
            real_errors = [e for e in errors if 'DEBUG' not in e]
            
            if real_errors:
                self.stdout.write(self.style.ERROR(f"\n🔴 КРИТИЧНЫХ ОШИБОК: {len(real_errors)}"))
                for i, error in enumerate(real_errors, 1):
                    self.stdout.write(f"   {i}. {error}")
                self.stdout.write(self.style.ERROR("\n⛔ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ!"))
            elif warnings:
                self.stdout.write(self.style.SUCCESS("\n✅ КРИТИЧНЫХ ОШИБОК НЕТ"))
            else:
                self.stdout.write(self.style.SUCCESS("\n✅ ВСЁ ОТЛИЧНО (локальная среда)!"))
        else:
            if errors:
                self.stdout.write(self.style.ERROR(f"\n🔴 КРИТИЧНЫХ ОШИБОК: {len(errors)}"))
                for i, error in enumerate(errors, 1):
                    self.stdout.write(f"   {i}. {error}")
                self.stdout.write(self.style.ERROR("\n⛔ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ!"))
            else:
                self.stdout.write(self.style.SUCCESS("\n✅ ВСЁ ИДЕАЛЬНО!"))
                self.stdout.write(self.style.SUCCESS("🚀 PROD ПОЛНОСТЬЮ ГОТОВ!"))
        
        if warnings:
            self.stdout.write(self.style.WARNING(f"\n🟡 ПРЕДУПРЕЖДЕНИЙ: {len(warnings)}"))
            for i, warning in enumerate(warnings, 1):
                self.stdout.write(f"   {i}. {warning}")
        
        if not settings.DEBUG:
            self.stdout.write("\n💡 LIGHTHOUSE:")
            self.stdout.write("   Запустите вручную: https://pagespeed.web.dev/")
        
        self.stdout.write("\n" + "="*70 + "\n")