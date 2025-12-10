# main/tests/production/test_prod_check.py
"""
🚀 PRODUCTION HEALTH CHECK
Безопасные тесты для продакшена - НЕ создают тестовую БД!

Запуск:
python manage.py test main.tests.production.test_prod_check --no-input
"""
from django.test import SimpleTestCase
from django.conf import settings
from django.db import connection
from django.core.management import call_command
from io import StringIO
import sys


class ProductionHealthCheck(SimpleTestCase):
    """
    SimpleTestCase НЕ создает test_py БД!
    Работает с реальной продакшн базой данных.
    """
    
    databases = '__all__'  # Разрешаем доступ к БД
    
    # ==========================================
    # 1. НАСТРОЙКИ DJANGO
    # ==========================================
    
    def test_01_debug_mode(self):
        """✅ DEBUG выключен на проде"""
        print("\n" + "="*60)
        print("1️⃣ ТЕСТ: DEBUG режим")
        print("="*60)
        
        if settings.DEBUG:
            print("❌ КРИТИЧНО: DEBUG=True на продакшене!")
            print("   Исправьте в .env: DEBUG=False")
            self.fail("DEBUG должен быть False на проде!")
        else:
            print("✅ DEBUG = False")
    
    def test_02_secret_key(self):
        """✅ SECRET_KEY настроен"""
        print("\n" + "="*60)
        print("2️⃣ ТЕСТ: SECRET_KEY")
        print("="*60)
        
        if not settings.SECRET_KEY:
            print("❌ КРИТИЧНО: SECRET_KEY не установлен!")
            self.fail("SECRET_KEY отсутствует!")
        
        if settings.SECRET_KEY == 'django-insecure-default-key':
            print("❌ КРИТИЧНО: Используется дефолтный SECRET_KEY!")
            self.fail("Смените SECRET_KEY!")
        
        print(f"✅ SECRET_KEY настроен ({len(settings.SECRET_KEY)} символов)")
    
    def test_03_allowed_hosts(self):
        """✅ ALLOWED_HOSTS настроен"""
        print("\n" + "="*60)
        print("3️⃣ ТЕСТ: ALLOWED_HOSTS")
        print("="*60)
        
        if not settings.ALLOWED_HOSTS:
            print("❌ КРИТИЧНО: ALLOWED_HOSTS пустой!")
            self.fail("Настройте ALLOWED_HOSTS!")
        
        if '*' in settings.ALLOWED_HOSTS and not settings.DEBUG:
            print("❌ КРИТИЧНО: ALLOWED_HOSTS='*' на проде!")
            self.fail("Укажите конкретные домены!")
        
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS[:5]}")
    
    def test_04_secure_cookies(self):
        """✅ Безопасные cookies"""
        print("\n" + "="*60)
        print("4️⃣ ТЕСТ: Безопасность cookies")
        print("="*60)
        
        if not settings.DEBUG:
            if not settings.SESSION_COOKIE_SECURE:
                print("❌ КРИТИЧНО: SESSION_COOKIE_SECURE=False")
                self.fail("Включите SESSION_COOKIE_SECURE!")
            
            if not settings.CSRF_COOKIE_SECURE:
                print("❌ КРИТИЧНО: CSRF_COOKIE_SECURE=False")
                self.fail("Включите CSRF_COOKIE_SECURE!")
            
            print("✅ SESSION_COOKIE_SECURE = True")
            print("✅ CSRF_COOKIE_SECURE = True")
        else:
            print("⚠️ DEBUG=True, пропускаем проверку")
    
    def test_05_timezone(self):
        """✅ Таймзона настроена"""
        print("\n" + "="*60)
        print("5️⃣ ТЕСТ: Таймзона")
        print("="*60)
        
        expected_timezone = 'Asia/Tashkent'
        
        if settings.TIME_ZONE != expected_timezone:
            print(f"❌ ПРОБЛЕМА: TIME_ZONE={settings.TIME_ZONE}")
            print(f"   Должно быть: {expected_timezone}")
            self.fail(f"Неправильная таймзона!")
        
        if not settings.USE_TZ:
            print("❌ КРИТИЧНО: USE_TZ=False")
            self.fail("Включите USE_TZ!")
        
        print(f"✅ TIME_ZONE = {settings.TIME_ZONE}")
        print(f"✅ USE_TZ = True")
    
    # ==========================================
    # 2. БАЗА ДАННЫХ
    # ==========================================
    
    def test_06_database_connection(self):
        """✅ Подключение к БД"""
        print("\n" + "="*60)
        print("6️⃣ ТЕСТ: Подключение к БД")
        print("="*60)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
                print(f"✅ БД подключена")
                print(f"   Версия: {version.split()[0]} {version.split()[1]}")
                
        except Exception as e:
            print(f"❌ КРИТИЧНО: Ошибка БД: {str(e)}")
            self.fail(f"Нет подключения к БД: {str(e)}")
    
    def test_07_database_tables(self):
        """✅ Все таблицы существуют"""
        print("\n" + "="*60)
        print("7️⃣ ТЕСТ: Таблицы БД")
        print("="*60)
        
        required_tables = [
            'main_product',
            'main_contactform',
            'main_news',
            'main_dealer',
            'main_vacancy',
            'main_amocrmtoken',
        ]
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                  AND tablename LIKE 'main_%'
                ORDER BY tablename
            """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = []
            for table in required_tables:
                if table in existing_tables:
                    print(f"✅ {table}")
                else:
                    print(f"❌ {table} - НЕ НАЙДЕНА!")
                    missing_tables.append(table)
            
            if missing_tables:
                self.fail(f"Отсутствуют таблицы: {missing_tables}")
            
            print(f"\n✅ Всего таблиц main_*: {len(existing_tables)}")
    
    def test_08_migrations_applied(self):
        """✅ Все миграции применены"""
        print("\n" + "="*60)
        print("8️⃣ ТЕСТ: Миграции")
        print("="*60)
        
        try:
            output = StringIO()
            call_command('showmigrations', '--plan', stdout=output)
            migrations_output = output.getvalue()
            
            # Проверяем, есть ли неприменённые миграции
            unapplied = [line for line in migrations_output.split('\n') if '[ ]' in line]
            
            if unapplied:
                print(f"❌ КРИТИЧНО: {len(unapplied)} миграций не применены!")
                for migration in unapplied[:5]:
                    print(f"   {migration}")
                self.fail(f"Примените миграции: python manage.py migrate")
            
            print("✅ Все миграции применены")
            
        except Exception as e:
            print(f"❌ Ошибка проверки миграций: {str(e)}")
            self.fail(str(e))
    
    # ==========================================
    # 3. ДАННЫЕ В БД
    # ==========================================
    
    def test_09_products_exist(self):
        """✅ Продукты есть в БД"""
        print("\n" + "="*60)
        print("9️⃣ ТЕСТ: Продукты")
        print("="*60)
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM main_product WHERE is_active=true")
            active_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM main_product")
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                print("❌ КРИТИЧНО: Нет продуктов в БД!")
                self.fail("Загрузите продукты!")
            
            print(f"✅ Всего продуктов: {total_count}")
            print(f"✅ Активных: {active_count}")
    
    def test_10_no_duplicate_slugs(self):
        """✅ Нет дубликатов slug"""
        print("\n" + "="*60)
        print("🔟 ТЕСТ: Дубликаты slug")
        print("="*60)
        
        tables_to_check = [
            ('main_product', 'Продукты'),
            ('main_news', 'Новости'),
        ]
        
        found_duplicates = False
        
        for table, name in tables_to_check:
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT slug, COUNT(*) as count
                    FROM {table}
                    GROUP BY slug
                    HAVING COUNT(*) > 1
                """)
                
                duplicates = cursor.fetchall()
                
                if duplicates:
                    print(f"❌ {name}: {len(duplicates)} дубликатов slug!")
                    for slug, count in duplicates[:3]:
                        print(f"   '{slug}' встречается {count} раз")
                    found_duplicates = True
                else:
                    print(f"✅ {name}: дубликатов нет")
        
        if found_duplicates:
            self.fail("Найдены дубликаты slug!")
    
    # ==========================================
    # 4. ПРОВЕРКА ДУБЛИКАТОВ ORDER
    # ==========================================
    
    def test_11_productfeature_order_duplicates(self):
        """✅ ProductFeature: дубликаты order"""
        print("\n" + "="*60)
        print("1️⃣1️⃣ ТЕСТ: ProductFeature order")
        print("="*60)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT product_id, "order", COUNT(*) as count
                FROM main_productfeature
                GROUP BY product_id, "order"
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 5
            """)
            
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"⚠️ ВНИМАНИЕ: Найдено {len(duplicates)} дубликатов:")
                for product_id, order, count in duplicates:
                    print(f"   product_id={product_id}, order={order}, count={count}")
                print("\n💡 Исправьте SQL скриптом (см. документацию)")
            else:
                print("✅ Дубликатов нет")
    
    def test_12_productparameter_order_duplicates(self):
        """✅ ProductParameter: дубликаты order"""
        print("\n" + "="*60)
        print("1️⃣2️⃣ ТЕСТ: ProductParameter order")
        print("="*60)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM (
                    SELECT product_id, category, "order", COUNT(*) as count
                    FROM main_productparameter
                    GROUP BY product_id, category, "order"
                    HAVING COUNT(*) > 1
                ) AS duplicates
            """)
            
            dup_count = cursor.fetchone()[0]
            
            if dup_count > 0:
                print(f"⚠️ ВНИМАНИЕ: Найдено {dup_count} дубликатов order")
                print("💡 Исправьте SQL скриптом (см. документацию)")
            else:
                print("✅ Дубликатов нет")
    
    def test_13_productcardspec_order_duplicates(self):
        """✅ ProductCardSpec: дубликаты order"""
        print("\n" + "="*60)
        print("1️⃣3️⃣ ТЕСТ: ProductCardSpec order")
        print("="*60)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT product_id, "order", COUNT(*) as count
                FROM main_productcardspec
                GROUP BY product_id, "order"
                HAVING COUNT(*) > 1
                LIMIT 5
            """)
            
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"⚠️ ВНИМАНИЕ: Найдено {len(duplicates)} дубликатов:")
                for product_id, order, count in duplicates:
                    print(f"   product_id={product_id}, order={order}, count={count}")
            else:
                print("✅ Дубликатов нет")
    
    # ==========================================
    # 5. amoCRM
    # ==========================================
    
    def test_14_amocrm_token_exists(self):
        """✅ Токен amoCRM настроен"""
        print("\n" + "="*60)
        print("1️⃣4️⃣ ТЕСТ: amoCRM токен")
        print("="*60)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT access_token, refresh_token, expires_at
                FROM main_amocrmtoken
                WHERE id = 1
            """)
            
            row = cursor.fetchone()
            
            if not row:
                print("❌ КРИТИЧНО: Токен не найден в БД!")
                print("💡 Запустите: python manage.py init_amocrm_tokens")
                self.fail("amoCRM токен не настроен!")
            
            access_token, refresh_token, expires_at = row
            
            if not access_token:
                print("❌ КРИТИЧНО: access_token пустой!")
                self.fail("Настройте amoCRM токен!")
            
            if not refresh_token:
                print("❌ КРИТИЧНО: refresh_token пустой!")
                self.fail("Настройте amoCRM токен!")
            
            print(f"✅ access_token: {access_token[:20]}...")
            print(f"✅ refresh_token: {refresh_token[:20]}...")
            print(f"✅ Истекает: {expires_at}")
            
            # Проверяем, не истёк ли токен
            from django.utils import timezone
            if expires_at < timezone.now():
                print("⚠️ ВНИМАНИЕ: Токен истёк!")
                print("💡 Он обновится автоматически при первом запросе")
    
    def test_15_amocrm_settings(self):
        """✅ Настройки amoCRM"""
        print("\n" + "="*60)
        print("1️⃣5️⃣ ТЕСТ: Настройки amoCRM")
        print("="*60)
        
        required_settings = [
            'AMOCRM_SUBDOMAIN',
            'AMOCRM_CLIENT_ID',
            'AMOCRM_CLIENT_SECRET',
            'AMOCRM_PIPELINE_ID',
            'AMOCRM_STATUS_ID',
        ]
        
        missing = []
        for setting_name in required_settings:
            value = getattr(settings, setting_name, None)
            if not value:
                print(f"❌ {setting_name} не установлен!")
                missing.append(setting_name)
            else:
                # Показываем только начало для безопасности
                display_value = str(value)[:20] if 'SECRET' not in setting_name else '***'
                print(f"✅ {setting_name} = {display_value}...")
        
        if missing:
            self.fail(f"Отсутствуют настройки: {missing}")
    
    # ==========================================
    # 6. СТАТИСТИКА
    # ==========================================
    
    def test_16_statistics(self):
        """📊 Статистика БД"""
        print("\n" + "="*60)
        print("1️⃣6️⃣ СТАТИСТИКА БД")
        print("="*60)
        
        stats = {}
        
        tables = [
            ('main_product', 'Продукты'),
            ('main_news', 'Новости'),
            ('main_dealer', 'Дилеры'),
            ('main_contactform', 'Заявки'),
            ('main_vacancy', 'Вакансии'),
        ]
        
        with connection.cursor() as cursor:
            for table, name in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[name] = count
                print(f"📊 {name}: {count}")
        
        # Проверяем минимальные требования
        if stats.get('Продукты', 0) == 0:
            print("\n❌ КРИТИЧНО: Нет продуктов!")
            self.fail("Загрузите продукты в БД!")
    
    # ==========================================
    # 7. ПРОВЕРКА СИСТЕМНЫХ КОМАНД
    # ==========================================
    
    def test_17_system_check(self):
        """✅ Django system check"""
        print("\n" + "="*60)
        print("1️⃣7️⃣ ТЕСТ: System check")
        print("="*60)
        
        try:
            output = StringIO()
            call_command('check', '--deploy', stdout=output, stderr=StringIO())
            result = output.getvalue()
            
            if 'System check identified no issues' in result:
                print("✅ System check: OK")
            elif 'System check identified some issues' in result:
                print("⚠️ ВНИМАНИЕ: Есть предупреждения")
                print(result[:500])
            else:
                print("❌ System check провалился!")
                print(result[:500])
                self.fail("System check нашёл проблемы!")
                
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            self.fail(str(e))
    
    # ==========================================
    # ФИНАЛЬНЫЙ ОТЧЁТ
    # ==========================================
    
    def test_99_final_report(self):
        """📊 Финальный отчёт"""
        print("\n" + "="*60)
        print("📊 ФИНАЛЬНЫЙ ОТЧЁТ")
        print("="*60)
        
        print("\n✅ Если вы видите это сообщение:")
        print("   → Все критичные проверки пройдены!")
        print("   → Сайт работает корректно на продакшене!")
        
        print("\n⚠️ ОБРАТИТЕ ВНИМАНИЕ:")
        print("   → Проверьте предупреждения выше (если есть)")
        print("   → Дубликаты order нужно исправить SQL скриптом")
        print("   → amoCRM токен обновляется автоматически")
        
        print("\n" + "="*60)
        print("🚀 PRODUCTION HEALTH CHECK ЗАВЕРШЁН!")
        print("="*60 + "\n")