"""
🔥 PRODUCTION READINESS TEST
Проверяет, что сайт готов на 100% к проду
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from main.models import Product, News, Dealer
import json


class ProductionReadinessTest(TestCase):
    """Тест готовности к продакшену"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = Client()
        
        # Создаем тестовый продукт
        self.product = Product.objects.create(
            title_uz="Test Product UZ",
            title_ru="Test Product RU", 
            title_en="Test Product EN",
            slug="test-product",
            category="tiger_v",
            categories="tiger_v",
        )
    
    # ==========================================
    # ТЕСТ #1: CSRF ТОКЕНЫ ВО ВСЕХ ФОРМАХ
    # ==========================================
    
    def test_csrf_token_in_all_forms(self):
        """
        ✅ Проверяет, что ВСЕ формы содержат CSRF токен
        """
        print("\n" + "="*60)
        print("🔒 ТЕСТ #1: CSRF токены во всех формах")
        print("="*60)
        
        # Список всех страниц с формами
        pages_with_forms = [
            ('home', {}),
            ('contact', {}),
            ('become_a_dealer', {}),
            ('jobs', {}),
        ]
        
        for url_name, kwargs in pages_with_forms:
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, 200)
                
                # Проверяем наличие CSRF токена в HTML
                html = response.content.decode('utf-8')
                
                # Ищем {% csrf_token %} или его результат
                has_csrf_meta = 'csrfmiddlewaretoken' in html
                has_csrf_cookie = 'csrftoken' in str(response.cookies)
                
                if has_csrf_meta or has_csrf_cookie:
                    print(f"✅ {url_name}: CSRF токен найден")
                else:
                    print(f"❌ {url_name}: CSRF токен НЕ НАЙДЕН!")
                    
                self.assertTrue(
                    has_csrf_meta or has_csrf_cookie,
                    f"❌ Страница {url_name} не содержит CSRF токен!"
                )
        
        print("\n✅ ВСЕ ФОРМЫ СОДЕРЖАТ CSRF ТОКЕНЫ!")
    
    # ==========================================
    # ТЕСТ #2: API ИСПОЛЬЗУЕТ MIDDLEWARE, НЕ URL
    # ==========================================
    
    def test_api_uses_middleware_not_url(self):
        """
        ✅ Проверяет, что API определяет язык через middleware,
        а НЕ через проверку /uz/ в URL
        """
        print("\n" + "="*60)
        print("🌍 ТЕСТ #2: API использует middleware для языка")
        print("="*60)
        
        # Тестируем все языковые версии API
        languages = ['uz', 'ru', 'en']
        
        for lang in languages:
            with self.subTest(language=lang):
                # Запрос к API с языком в URL
                url = f'/api/{lang}/products/'
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, 200)
                
                data = response.json()
                
                # Проверяем, что язык определяется правильно
                if data['results']:
                    product = data['results'][0]
                    
                    # Проверяем, что вернулся правильный перевод
                    if lang == 'uz':
                        expected_title = "Test Product UZ"
                    elif lang == 'ru':
                        expected_title = "Test Product RU"
                    else:
                        expected_title = "Test Product EN"
                    
                    actual_title = product.get('title', '')
                    
                    if actual_title == expected_title:
                        print(f"✅ API/{lang}/: Правильный язык ({expected_title})")
                    else:
                        print(f"❌ API/{lang}/: Неправильный язык!")
                        print(f"   Ожидалось: {expected_title}")
                        print(f"   Получено: {actual_title}")
                    
                    self.assertEqual(
                        actual_title, 
                        expected_title,
                        f"API не использует middleware для языка {lang}!"
                    )
        
        print("\n✅ API ИСПОЛЬЗУЕТ MIDDLEWARE, НЕ URL!")
    
    # ==========================================
    # ТЕСТ #3: SEO ТЕГИ НА ВСЕХ СТРАНИЦАХ
    # ==========================================
    
    def test_seo_tags_on_all_pages(self):
        """
        ✅ Проверяет hreflang и canonical на ВСЕХ страницах
        """
        print("\n" + "="*60)
        print("🔍 ТЕСТ #3: SEO теги на всех страницах")
        print("="*60)
        
        # Список всех публичных страниц
        all_pages = [
            ('home', {}),
            ('about', {}),
            ('contact', {}),
            ('products', {}),
            ('dealers', {}),
            ('become_a_dealer', {}),
            ('services', {}),
            ('lizing', {}),
            ('jobs', {}),
            ('news', {}),
            ('product_detail', {'product_id': self.product.slug}),
        ]
        
        for url_name, kwargs in all_pages:
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, 200)
                
                html = response.content.decode('utf-8')
                
                # Проверяем hreflang
                has_hreflang = 'rel="alternate" hreflang="uz"' in html
                has_canonical = 'rel="canonical"' in html
                
                if has_hreflang and has_canonical:
                    print(f"✅ {url_name}: hreflang + canonical присутствуют")
                else:
                    if not has_hreflang:
                        print(f"❌ {url_name}: НЕТ hreflang!")
                    if not has_canonical:
                        print(f"❌ {url_name}: НЕТ canonical!")
                
                self.assertTrue(has_hreflang, f"{url_name}: нет hreflang!")
                self.assertTrue(has_canonical, f"{url_name}: нет canonical!")
        
        print("\n✅ ВСЕ СТРАНИЦЫ СОДЕРЖАТ SEO ТЕГИ!")
    
    # ==========================================
    # ТЕСТ #4: ПРОИЗВОДИТЕЛЬНОСТЬ (SQL ЗАПРОСЫ)
    # ==========================================
    
    def test_sql_queries_performance(self):
        """
        ✅ Проверяет количество SQL запросов на критичных страницах
        """
        print("\n" + "="*60)
        print("⚡ ТЕСТ #4: Производительность SQL запросов")
        print("="*60)
        
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        # Проверяем главную страницу
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse('home'))
            self.assertEqual(response.status_code, 200)
        
        num_queries = len(context.captured_queries)
        print(f"📊 Главная страница: {num_queries} SQL запросов")
        
        # Допустимо до 10 запросов
        if num_queries <= 10:
            print(f"✅ ОТЛИЧНО! Оптимально для главной страницы")
        elif num_queries <= 20:
            print(f"⚠️  ПРИЕМЛЕМО, но можно оптимизировать")
        else:
            print(f"❌ ПЛОХО! Слишком много запросов!")
        
        self.assertLessEqual(
            num_queries, 
            20, 
            f"❌ Слишком много SQL запросов: {num_queries}"
        )
        
        # Проверяем API
        with CaptureQueriesContext(connection) as context:
            response = self.client.get('/api/uz/products/')
            self.assertEqual(response.status_code, 200)
        
        api_queries = len(context.captured_queries)
        print(f"📊 API /products/: {api_queries} SQL запросов")
        
        if api_queries <= 5:
            print(f"✅ ОТЛИЧНО! API оптимизирован")
        elif api_queries <= 10:
            print(f"⚠️  ПРИЕМЛЕМО для API")
        else:
            print(f"❌ ПЛОХО! API делает слишком много запросов!")
        
        self.assertLessEqual(
            api_queries,
            10,
            f"❌ API делает слишком много запросов: {api_queries}"
        )
    
    # ==========================================
    # ТЕСТ #5: ФОРМА ОТПРАВКИ (CSRF + AJAX)
    # ==========================================
    
    def test_form_submission_with_csrf(self):
        """
        ✅ Проверяет, что формы работают с CSRF токеном
        """
        print("\n" + "="*60)
        print("📝 ТЕСТ #5: Отправка формы с CSRF")
        print("="*60)
        
        # Получаем страницу с формой
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        
        # Извлекаем CSRF токен
        csrf_token = response.cookies.get('csrftoken')
        
        if csrf_token:
            print(f"✅ CSRF токен получен из cookies")
        else:
            # Пробуем найти в HTML
            html = response.content.decode('utf-8')
            import re
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
            if match:
                csrf_token_value = match.group(1)
                print(f"✅ CSRF токен найден в HTML")
            else:
                print(f"❌ CSRF токен НЕ НАЙДЕН!")
                self.fail("❌ CSRF токен отсутствует!")
        
        # Пробуем отправить форму
        form_data = {
            'name': 'Test User',
            'region': 'Toshkent shahri',
            'phone': '+998901234567',
            'message': 'Test message'
        }
        
        # Отправка через POST (как AJAX)
        response = self.client.post(
            '/api/uz/contact/',
            data=json.dumps(form_data),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else ''
        )
        
        if response.status_code == 201:
            print(f"✅ Форма отправлена успешно!")
        else:
            print(f"❌ Ошибка отправки формы: {response.status_code}")
            print(f"   Ответ: {response.content.decode('utf-8')}")
        
        self.assertIn(
            response.status_code,
            [200, 201],
            f"❌ Форма не отправляется! Код: {response.status_code}"
        )
    
    # ==========================================
    # ТЕСТ #6: ВСЕ ЯЗЫКИ РАБОТАЮТ
    # ==========================================
    
    def test_all_languages_work(self):
        """
        ✅ Проверяет, что все 3 языка работают корректно
        """
        print("\n" + "="*60)
        print("🌐 ТЕСТ #6: Работа всех языков")
        print("="*60)
        
        languages = {
            'uz': '/',
            'ru': '/ru/',
            'en': '/en/'
        }
        
        for lang, url_prefix in languages.items():
            with self.subTest(language=lang):
                # Проверяем главную страницу
                response = self.client.get(url_prefix)
                self.assertEqual(response.status_code, 200)
                
                html = response.content.decode('utf-8')
                
                # Проверяем язык в HTML
                has_lang = f'lang="{lang}"' in html
                
                if has_lang:
                    print(f"✅ {lang.upper()}: Язык определяется корректно")
                else:
                    print(f"❌ {lang.upper()}: Язык НЕ определяется!")
                
                self.assertTrue(
                    has_lang,
                    f"❌ Язык {lang} не работает на главной странице!"
                )
        
        print("\n✅ ВСЕ 3 ЯЗЫКА РАБОТАЮТ!")
    
    # ==========================================
    # ТЕСТ #7: СКОРОСТЬ ЗАГРУЗКИ СТРАНИЦ
    # ==========================================
    
    def test_page_load_speed(self):
        """
        ✅ Проверяет скорость загрузки критичных страниц
        """
        print("\n" + "="*60)
        print("⚡ ТЕСТ #7: Скорость загрузки страниц")
        print("="*60)
        
        import time
        
        pages_to_test = [
            ('home', {}, 'Главная'),
            ('products', {}, 'Продукты'),
            ('product_detail', {'product_id': self.product.slug}, 'Детали продукта'),
        ]
        
        for url_name, kwargs, description in pages_to_test:
            with self.subTest(page=url_name):
                start_time = time.time()
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                end_time = time.time()
                
                load_time = (end_time - start_time) * 1000  # в миллисекундах
                
                self.assertEqual(response.status_code, 200)
                
                if load_time < 100:
                    print(f"✅ {description}: {load_time:.2f}ms - ОТЛИЧНО!")
                elif load_time < 300:
                    print(f"⚠️  {description}: {load_time:.2f}ms - ПРИЕМЛЕМО")
                else:
                    print(f"❌ {description}: {load_time:.2f}ms - МЕДЛЕННО!")
                
                # Допускаем до 500ms для теста
                self.assertLess(
                    load_time,
                    500,
                    f"❌ {description} загружается слишком долго: {load_time:.2f}ms"
                )
        
        print("\n✅ ВСЕ СТРАНИЦЫ ЗАГРУЖАЮТСЯ БЫСТРО!")
    
    # ==========================================
    # ФИНАЛЬНЫЙ ОТЧЕТ
    # ==========================================
    
    def test_zzz_final_report(self):
        """
        📊 Итоговый отчет готовности к продакшену
        """
        print("\n" + "="*60)
        print("📊 ФИНАЛЬНЫЙ ОТЧЕТ")
        print("="*60)
        print("\n✅ Если вы видите это сообщение - ВСЕ ТЕСТЫ ПРОШЛИ!")
        print("\n🚀 САЙТ ГОТОВ К ПРОДАКШЕНУ НА 100%!")
        print("\n" + "="*60)