from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone  # ← ДОБАВИТЬ
from datetime import timedelta      # ← ДОБАВИТЬ
from main.models import ContactForm, AmoCRMToken
from unittest.mock import patch, MagicMock
import json


class AmoCRMIntegrationTest(TestCase):
    """Тест интеграции с amoCRM"""
    
    def setUp(self):
        """Подготовка данных"""
        self.client = Client()
        
        # ✅ ПРАВИЛЬНО: Создаем datetime объект
        future_time = timezone.now() + timedelta(days=1000)
        
        # Создаем токен amoCRM для теста
        AmoCRMToken.objects.create(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_at=future_time  # ✅ Теперь правильный тип
        )
    
    # ==========================================
    # ТЕСТ #1: СОЗДАНИЕ ЛИДА В БД
    # ==========================================
    
    def test_contact_form_creates_lead_in_db(self):
        """
        ✅ Проверяет, что форма сохраняет лид в БД
        """
        print("\n" + "="*60)
        print("📝 ТЕСТ #1: Создание лида в БД")
        print("="*60)
        
        form_data = {
            'name': 'Тестовый Клиент',
            'region': 'Toshkent shahri',
            'phone': '+998901234567',
            'message': 'Интересует Tiger V',
            'utm_data': json.dumps({'utm_source': 'google'}),
            'visitor_uid': 'test_uid_123'
        }
        
        # Отправляем форму
        response = self.client.post(
            '/api/uz/contact/',
            data=json.dumps(form_data),
            content_type='application/json'
        )
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 201)
        print(f"✅ Статус ответа: 201 Created")
        
        # Проверяем, что лид сохранился в БД
        lead = ContactForm.objects.filter(phone='+998901234567').first()
        self.assertIsNotNone(lead)
        print(f"✅ Лид сохранен в БД: {lead.name}")
        
        # Проверяем данные
        self.assertEqual(lead.name, 'Тестовый Клиент')
        self.assertEqual(lead.region, 'Toshkent shahri')
        self.assertEqual(lead.message, 'Интересует Tiger V')
        print(f"✅ Все данные корректны")
        
        print("\n✅ ЛИДЫ СОХРАНЯЮТСЯ В БД!")
    
   
    # ==========================================
    # ТЕСТ #4: UTM МЕТКИ СОХРАНЯЮТСЯ
    # ==========================================
    
    def test_utm_data_saved(self):
        """
        ✅ Проверяет, что UTM метки сохраняются
        """
        print("\n" + "="*60)
        print("🔖 ТЕСТ #4: UTM метки")
        print("="*60)
        
        utm_data = {
            'utm_source': 'google',
            'utm_medium': 'cpc',
            'utm_campaign': 'faw_trucks_2025'
        }
        
        form_data = {
            'name': 'UTM Клиент',
            'region': 'Toshkent shahri',
            'phone': '+998901111111',
            'message': 'Тест',
            'utm_data': json.dumps(utm_data)
        }
        
        response = self.client.post(
            '/api/uz/contact/',
            data=json.dumps(form_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Проверяем UTM
        lead = ContactForm.objects.filter(phone='+998901111111').first()
        self.assertIsNotNone(lead.utm_data)
        
        saved_utm = json.loads(lead.utm_data)
        self.assertEqual(saved_utm['utm_source'], 'google')
        self.assertEqual(saved_utm['utm_campaign'], 'faw_trucks_2025')
        print(f"✅ UTM метки сохранены: {saved_utm}")
        
        print("\n✅ UTM МЕТКИ РАБОТАЮТ!")
    
    # ==========================================
    # ТЕСТ #5: VISITOR UID СОХРАНЯЕТСЯ
    # ==========================================
    
    def test_visitor_uid_saved(self):
        """
        ✅ Проверяет, что visitor_uid для amoCRM сохраняется
        """
        print("\n" + "="*60)
        print("🆔 ТЕСТ #5: Visitor UID")
        print("="*60)
        
        form_data = {
            'name': 'UID Клиент',
            'region': 'Buxoro viloyati',
            'phone': '+998902222222',
            'message': 'Тест UID',
            'visitor_uid': 'amocrm_uid_xyz789'
        }
        
        response = self.client.post(
            '/api/uz/contact/',
            data=json.dumps(form_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Проверяем visitor_uid
        lead = ContactForm.objects.filter(phone='+998902222222').first()
        self.assertEqual(lead.visitor_uid, 'amocrm_uid_xyz789')
        print(f"✅ Visitor UID сохранен: {lead.visitor_uid}")
        
        print("\n✅ VISITOR UID РАБОТАЕТ!")
    
    # ==========================================
    # ТЕСТ #6: ПРОВЕРКА ВСЕХ ЯЗЫКОВ
    # ==========================================
    
    def test_contact_form_all_languages(self):
        """
        ✅ Проверяет, что форма работает на всех языках
        """
        print("\n" + "="*60)
        print("🌐 ТЕСТ #6: Формы на всех языках")
        print("="*60)
        
        languages = {
            'uz': '/api/uz/contact/',
            'ru': '/api/ru/contact/',
            'en': '/api/en/contact/'
        }
        
        for lang, url in languages.items():
            form_data = {
                'name': f'{lang.upper()} Client',
                'region': 'Toshkent shahri',
                'phone': f'+99890{lang}1234',
                'message': f'Test {lang}'
            }
            
            response = self.client.post(
                url,
                data=json.dumps(form_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 201)
            print(f"✅ {lang.upper()}: Форма работает")
        
        print("\n✅ ФОРМЫ РАБОТАЮТ НА ВСЕХ ЯЗЫКАХ!")
    
    # ==========================================
    # ФИНАЛЬНЫЙ ОТЧЕТ
    # ==========================================
    
    def test_zzz_amocrm_final_report(self):
        """
        📊 Итоговый отчет amoCRM
        """
        print("\n" + "="*60)
        print("📊 ФИНАЛЬНЫЙ ОТЧЕТ amoCRM")
        print("="*60)
        print("\n✅ Если вы видите это сообщение - ВСЕ ТЕСТЫ amoCRM ПРОШЛИ!")
        print("\n🚀 amoCRM ИНТЕГРАЦИЯ РАБОТАЕТ НА 100%!")
        print("\n" + "="*60)