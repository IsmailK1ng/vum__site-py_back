# main/tests/test_dashboard.py

import json
from datetime import timedelta
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import connection
from django.test.utils import CaptureQueriesContext
from main.models import ContactForm, Dashboard
from main.admin import DashboardAdmin
from django.contrib.admin.sites import AdminSite


class DashboardTestCase(TestCase):
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Создаём тестовый AdminSite
        self.admin_site = AdminSite()
        self.dashboard_admin = DashboardAdmin(Dashboard, self.admin_site)
        
        # Создаём тестовые данные
        self.create_test_data()
    
    def create_test_data(self):
        """Создаём тестовые заявки"""
        today = timezone.now()
        
        for i in range(10):
            ContactForm.objects.create(
                name=f'Test User {i}',
                phone=f'+998901234{i:03d}',
                product='FAW CA3252',
                region='Toshkent shahri',
                amocrm_status='sent',
                created_at=today - timedelta(days=i)
            )
    
    def test_changelist_view_queries(self):
        """ТЕСТ 1: Проверка запросов в changelist_view"""
        print("\n" + "="*80)
        print("📋 ТЕСТ 1: CHANGELIST_VIEW - ЗАПРОСЫ К БД")
        print("="*80)
        
        request = self.factory.get('/admin/main/dashboard/')
        request.user = self.user
        
        with CaptureQueriesContext(connection) as ctx:
            response = self.dashboard_admin.changelist_view(request)
        
        query_count = len(ctx.captured_queries)
        
        print(f"\n✅ Статус ответа: {response.status_code}")
        print(f"📊 Количество SQL запросов: {query_count}")
        
        if query_count > 0:
            print(f"\n❌ ПРОБЛЕМА: Django делает {query_count} запросов к БД!")
            print("Первые 3 запроса:")
            for i, query in enumerate(ctx.captured_queries[:3], 1):
                print(f"  {i}. {query['sql'][:100]}...")
        else:
            print("✅ Django НЕ делает запросов к БД (только рендерит HTML)")
    
    def test_changelist_view_with_filters(self):
        """ТЕСТ 2: Проверка запросов при фильтрации"""
        print("\n" + "="*80)
        print("📋 ТЕСТ 2: CHANGELIST_VIEW С ФИЛЬТРАМИ")
        print("="*80)
        
        today = timezone.now()
        week_ago = today - timedelta(days=7)
        
        request = self.factory.get('/admin/main/dashboard/', {
            'date_from': week_ago.strftime('%Y-%m-%d'),
            'date_to': today.strftime('%Y-%m-%d'),
            'region': 'Toshkent shahri'
        })
        request.user = self.user
        
        with CaptureQueriesContext(connection) as ctx:
            response = self.dashboard_admin.changelist_view(request)
        
        query_count = len(ctx.captured_queries)
        
        print(f"\n✅ Статус ответа: {response.status_code}")
        print(f"📊 Количество SQL запросов: {query_count}")
        
        if query_count > 0:
            print(f"\n❌ ПРОБЛЕМА: Django делает {query_count} запросов к БД!")
        else:
            print("✅ Django НЕ делает запросов к БД")
    
    def test_api_endpoint(self):
        """ТЕСТ 3: Проверка API endpoint"""
        print("\n" + "="*80)
        print("📋 ТЕСТ 3: API ENDPOINT (/api/data/)")
        print("="*80)
        
        today = timezone.now()
        week_ago = today - timedelta(days=7)
        
        request = self.factory.get('/admin/main/dashboard/api/data/', {
            'date_from': week_ago.strftime('%Y-%m-%d'),
            'date_to': today.strftime('%Y-%m-%d'),
        })
        request.user = self.user
        
        with CaptureQueriesContext(connection) as ctx:
            response = self.dashboard_admin.dashboard_api_data(request)
        
        query_count = len(ctx.captured_queries)
        
        print(f"\n✅ Статус ответа: {response.status_code}")
        print(f"📊 Количество SQL запросов: {query_count}")
        
        if query_count > 0:
            print(f"\n✅ ПРАВИЛЬНО: API делает {query_count} запросов к БД")
            
            # Группируем запросы
            select_queries = [q for q in ctx.captured_queries if 'SELECT' in q['sql']]
            print(f"  - SELECT запросов: {len(select_queries)}")
        
        # Проверяем ответ
        data = json.loads(response.content)
        
        if data.get('success'):
            print(f"\n✅ API вернул успешный ответ")
            print(f"  - Всего заявок: {data['kpi']['total_leads']}")
            print(f"  - Конверсия amoCRM: {data['kpi']['amocrm_conversion']}%")
        else:
            print(f"\n❌ API вернул ошибку: {data.get('error')}")
    
    def test_duplication_check(self):
        """ТЕСТ 4: Проверка дублирования запросов"""
        print("\n" + "="*80)
        print("📋 ТЕСТ 4: ПРОВЕРКА ДУБЛИРОВАНИЯ ЗАПРОСОВ")
        print("="*80)
        
        today = timezone.now()
        week_ago = today - timedelta(days=7)
        
        # Запросы через changelist_view
        request1 = self.factory.get('/admin/main/dashboard/', {
            'date_from': week_ago.strftime('%Y-%m-%d'),
            'date_to': today.strftime('%Y-%m-%d'),
        })
        request1.user = self.user
        
        with CaptureQueriesContext(connection) as ctx1:
            self.dashboard_admin.changelist_view(request1)
        
        # Запросы через API
        request2 = self.factory.get('/admin/main/dashboard/api/data/', {
            'date_from': week_ago.strftime('%Y-%m-%d'),
            'date_to': today.strftime('%Y-%m-%d'),
        })
        request2.user = self.user
        
        with CaptureQueriesContext(connection) as ctx2:
            self.dashboard_admin.dashboard_api_data(request2)
        
        changelist_queries = len(ctx1.captured_queries)
        api_queries = len(ctx2.captured_queries)
        total_queries = changelist_queries + api_queries
        
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"  - Django changelist_view: {changelist_queries} запросов")
        print(f"  - API endpoint: {api_queries} запросов")
        print(f"  - ИТОГО при перезагрузке: {total_queries} запросов")
        
        if changelist_queries > 0 and api_queries > 0:
            print(f"\n❌ ДУБЛИРОВАНИЕ: При применении фильтра идёт {total_queries} запросов!")
            print("   (Django рендерит HTML + JS делает AJAX)")
        elif changelist_queries == 0 and api_queries > 0:
            print(f"\n✅ НЕТ ДУБЛИРОВАНИЯ: Только API делает запросы ({api_queries})")
        elif changelist_queries > 0 and api_queries == 0:
            print(f"\n✅ НЕТ ДУБЛИРОВАНИЯ: Только Django делает запросы ({changelist_queries})")
        else:
            print(f"\n⚠️ СТРАННО: Никто не делает запросы!")
        
        # ФИНАЛЬНЫЙ ВЫВОД
        print("\n" + "="*80)
        print("📊 ФИНАЛЬНЫЙ ВЫВОД")
        print("="*80)
        
        if changelist_queries == 0:
            print("✅ ПРАВИЛЬНО: Django НЕ вызывает аналитику в changelist_view")
            print("   → Данные загружаются только через AJAX")
        else:
            print("❌ НЕПРАВИЛЬНО: Django вызывает аналитику в changelist_view")
            print("   → Нужно убрать вызов analytics из changelist_view")
        
        if api_queries > 0:
            print("✅ ПРАВИЛЬНО: API endpoint работает и делает запросы к БД")
        else:
            print("❌ НЕПРАВИЛЬНО: API endpoint не делает запросы")
        
        print("\n" + "="*80)
    
    def test_filters_work(self):
        """ТЕСТ 5: Проверка работы фильтров"""
        print("\n" + "="*80)
        print("📋 ТЕСТ 5: ПРОВЕРКА ФИЛЬТРОВ")
        print("="*80)
        
        # ✅ ОЧИЩАЕМ ВСЕ СТАРЫЕ ЗАЯВКИ
        ContactForm.objects.all().delete()
        
        # Создаём заявки из разных регионов
        ContactForm.objects.create(
            name='Test Tashkent',
            phone='+998901111111',
            region='Toshkent shahri',
            product='FAW CA3252',
            amocrm_status='sent',
            created_at=timezone.now()
        )
        
        ContactForm.objects.create(
            name='Test Samarkand',
            phone='+998902222222',
            region='Samarqand viloyati',
            product='FAW J6',
            amocrm_status='sent',
            created_at=timezone.now()
        )
        
        # Фильтр по Ташкенту
        request = self.factory.get('/admin/main/dashboard/api/data/', {
            'date_from': timezone.now().strftime('%Y-%m-%d'),
            'date_to': timezone.now().strftime('%Y-%m-%d'),
            'region': 'Toshkent shahri'
        })
        request.user = self.user
        
        response = self.dashboard_admin.dashboard_api_data(request)
        data = json.loads(response.content)
        
        print(f"\n✅ Всего заявок: {data['kpi']['total_leads']}")
        print(f"✅ Ожидается: 1 (только Ташкент)")
        
        assert data['kpi']['total_leads'] == 1, f"Фильтр по региону не работает! Получено: {data['kpi']['total_leads']}"
        print("✅ Фильтр по региону работает правильно!")
    
    def test_performance(self):
        """ТЕСТ 6: Проверка производительности"""
        import time
        
        print("\n" + "="*80)
        print("📋 ТЕСТ 6: ПРОВЕРКА ПРОИЗВОДИТЕЛЬНОСТИ")
        print("="*80)
        
        # Создаём 1000 заявок
        bulk_data = []
        for i in range(1000):
            bulk_data.append(ContactForm(
                name=f'Test User {i}',
                phone=f'+99890{i:07d}',
                product='FAW CA3252',
                region='Toshkent shahri',
                created_at=timezone.now()
            ))
        ContactForm.objects.bulk_create(bulk_data)
        
        request = self.factory.get('/admin/main/dashboard/api/data/', {
            'date_from': timezone.now().strftime('%Y-%m-%d'),
            'date_to': timezone.now().strftime('%Y-%m-%d'),
        })
        request.user = self.user
        
        # Замеряем время
        start = time.time()
        response = self.dashboard_admin.dashboard_api_data(request)
        end = time.time()
        
        elapsed = end - start
        
        print(f"\n⏱️ Время ответа API: {elapsed:.2f} секунд")
        print(f"📊 Заявок обработано: 1000")
        
        if elapsed < 1.0:
            print("✅ ОТЛИЧНО: Ответ менее 1 секунды")
        elif elapsed < 3.0:
            print("⚠️ ПРИЕМЛЕМО: Ответ 1-3 секунды")
        else:
            print("❌ МЕДЛЕННО: Ответ более 3 секунд — нужна оптимизация!")
    
    def test_insights_generation(self):
        """ТЕСТ 7: Проверка генерации инсайтов"""
        print("\n" + "="*80)
        print("📋 ТЕСТ 7: ПРОВЕРКА ИНСАЙТОВ")
        print("="*80)
        
        # Создаём заявки с хорошей конверсией
        for i in range(10):
            ContactForm.objects.create(
                name=f'Test {i}',
                phone=f'+99890{i:07d}',
                product='FAW CA3252',
                region='Toshkent shahri',
                amocrm_status='sent',  # ← Отправлены в amoCRM
                created_at=timezone.now()
            )
        
        request = self.factory.get('/admin/main/dashboard/api/data/', {
            'date_from': timezone.now().strftime('%Y-%m-%d'),
            'date_to': timezone.now().strftime('%Y-%m-%d'),
        })
        request.user = self.user
        
        response = self.dashboard_admin.dashboard_api_data(request)
        data = json.loads(response.content)
        
        insights = data['insights']
        
        print(f"\n✅ Позитивных инсайтов: {len(insights['good'])}")
        print(f"⚠️ Проблем: {len(insights['problems'])}")
        print(f"🎯 Рекомендаций: {len(insights['recommendations'])}")
        
        # Проверяем что инсайты не пустые
        total_insights = len(insights['good']) + len(insights['problems']) + len(insights['recommendations'])
        
        assert total_insights > 0, "Инсайты не генерируются!"
        print("✅ Инсайты генерируются правильно!")
    
    def test_excel_export(self):
        """ТЕСТ 8: Проверка экспорта в Excel"""
        print("\n" + "="*80)
        print("📋 ТЕСТ 8: ПРОВЕРКА ЭКСПОРТА EXCEL")
        print("="*80)
        
        request = self.factory.get('/admin/main/dashboard/export/excel/', {
            'date_from': timezone.now().strftime('%Y-%m-%d'),
            'date_to': timezone.now().strftime('%Y-%m-%d'),
        })
        request.user = self.user
        
        response = self.dashboard_admin.dashboard_export_excel(request)
        
        print(f"\n✅ Статус ответа: {response.status_code}")
        print(f"📄 Content-Type: {response['Content-Type']}")
        
        assert response.status_code == 200, "Экспорт не работает!"
        
        # ✅ ИСПРАВЛЯЕМ ПРОВЕРКУ
        assert 'spreadsheet' in response['Content-Type'] or 'excel' in response['Content-Type'].lower(), \
            f"Не Excel файл! Content-Type: {response['Content-Type']}"
        
        print("✅ Excel экспорт работает!")

    def test_product_filter(self):
        """ТЕСТ 9: Проверка фильтра по модели"""
        print("\n" + "="*80)
        print("📋 ТЕСТ 9: ПРОВЕРКА ФИЛЬТРА ПО МОДЕЛИ")
        print("="*80)
        
        # Очищаем
        ContactForm.objects.all().delete()
        
        # Создаём заявки на разные модели
        ContactForm.objects.create(
            name='Test 1',
            phone='+998901111111',
            product='FAW CA3252',
            region='Toshkent shahri',
            amocrm_status='sent',
            created_at=timezone.now()
        )
        
        ContactForm.objects.create(
            name='Test 2',
            phone='+998902222222',
            product='FAW J6',
            region='Toshkent shahri',
            amocrm_status='sent',
            created_at=timezone.now()
        )
        
        ContactForm.objects.create(
            name='Test 3',
            phone='+998903333333',
            product='FAW CA3252',
            region='Toshkent shahri',
            amocrm_status='sent',
            created_at=timezone.now()
        )
        
        # Фильтр по FAW CA3252
        request = self.factory.get('/admin/main/dashboard/api/data/', {
            'date_from': timezone.now().strftime('%Y-%m-%d'),
            'date_to': timezone.now().strftime('%Y-%m-%d'),
            'product': 'FAW CA3252'
        })
        request.user = self.user
        
        response = self.dashboard_admin.dashboard_api_data(request)
        data = json.loads(response.content)
        
        print(f"\n✅ Всего заявок: {data['kpi']['total_leads']}")
        print(f"✅ Ожидается: 2 (только FAW CA3252)")
        
        assert data['kpi']['total_leads'] == 2, f"Фильтр по модели не работает! Получено: {data['kpi']['total_leads']}"
        print("✅ Фильтр по модели работает правильно!")

    def test_source_filter(self):
        """ТЕСТ 10: Проверка фильтра по источнику"""
        print("\n" + "="*80)
        print("📋 ТЕСТ 10: ПРОВЕРКА ФИЛЬТРА ПО ИСТОЧНИКУ")
        print("="*80)
        
        # Очищаем
        ContactForm.objects.all().delete()
        
        # Создаём заявки с разными источниками
        ContactForm.objects.create(
            name='Test Google',
            phone='+998901111111',
            product='FAW CA3252',
            region='Toshkent shahri',
            amocrm_status='sent',
            utm_data='{"utm_source":"google","utm_medium":"cpc"}',
            created_at=timezone.now()
        )
        
        ContactForm.objects.create(
            name='Test Instagram',
            phone='+998902222222',
            product='FAW J6',
            region='Toshkent shahri',
            amocrm_status='sent',
            utm_data='{"utm_source":"instagram","utm_medium":"social"}',
            created_at=timezone.now()
        )
        
        ContactForm.objects.create(
            name='Test Direct',
            phone='+998903333333',
            product='FAW CA3252',
            region='Toshkent shahri',
            amocrm_status='sent',
            utm_data='',  # Прямой заход
            created_at=timezone.now()
        )
        
        # Фильтр по Google
        request = self.factory.get('/admin/main/dashboard/api/data/', {
            'date_from': timezone.now().strftime('%Y-%m-%d'),
            'date_to': timezone.now().strftime('%Y-%m-%d'),
            'source': 'google'
        })
        request.user = self.user
        
        response = self.dashboard_admin.dashboard_api_data(request)
        data = json.loads(response.content)
        
        print(f"\n✅ Всего заявок: {data['kpi']['total_leads']}")
        print(f"✅ Ожидается: 1 (только Google)")
        
        assert data['kpi']['total_leads'] == 1, f"Фильтр по источнику не работает! Получено: {data['kpi']['total_leads']}"
        print("✅ Фильтр по источнику работает правильно!")
        
        # Фильтр по прямым заходам
        request2 = self.factory.get('/admin/main/dashboard/api/data/', {
            'date_from': timezone.now().strftime('%Y-%m-%d'),
            'date_to': timezone.now().strftime('%Y-%m-%d'),
            'source': 'direct'
        })
        request2.user = self.user
        
        response2 = self.dashboard_admin.dashboard_api_data(request2)
        data2 = json.loads(response2.content)
        
        print(f"\n✅ Прямых заходов: {data2['kpi']['total_leads']}")
        print(f"✅ Ожидается: 1")
        
        assert data2['kpi']['total_leads'] == 1, f"Фильтр по прямым заходам не работает! Получено: {data2['kpi']['total_leads']}"
        print("✅ Фильтр по прямым заходам работает правильно!")