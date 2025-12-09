"""
🚀 ФИНАЛЬНЫЙ ИНТЕГРАЦИОННЫЙ ТЕСТ
Проверяет весь пользовательский путь
"""
from django.test import TestCase, Client
from django.urls import reverse
from main.models import ContactForm
import json


class FinalIntegrationTest(TestCase):
    """Финальный тест перед продом"""
    
    def setUp(self):
        self.client = Client()
    
    def test_complete_user_journey(self):
        """
        ✅ Полный путь пользователя: от главной до отправки формы
        """
        print("\n" + "="*60)
        print("🚀 ФИНАЛЬНЫЙ ТЕСТ: Путь пользователя")
        print("="*60)
        
        # ШАГ 1: Открываем главную страницу
        print("\n📍 ШАГ 1: Главная страница")
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        print("✅ Главная открывается")
        
        # ШАГ 2: Проверяем SEO теги
        html = response.content.decode('utf-8')
        self.assertIn('rel="canonical"', html)
        self.assertIn('hreflang', html)
        print("✅ SEO теги присутствуют")
        
        # ШАГ 3: Открываем страницу продукта
        print("\n📍 ШАГ 2: Страница продуктов")
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)
        print("✅ Продукты открываются")
        
        # ШАГ 4: Открываем страницу контактов
        print("\n📍 ШАГ 3: Страница контактов")
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие формы
        html = response.content.decode('utf-8')
        self.assertIn('csrfmiddlewaretoken', html)
        print("✅ Форма контактов с CSRF")
        
        # ШАГ 5: Отправляем форму
        print("\n📍 ШАГ 4: Отправка формы")
        form_data = {
            'name': 'Интеграционный Тест',
            'region': 'Toshkent shahri',
            'phone': '+998901234567',
            'message': 'Полный тест системы',
            'utm_data': json.dumps({'utm_source': 'integration_test'})
        }
        
        response = self.client.post(
            '/api/uz/contact/',
            data=json.dumps(form_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        print("✅ Форма отправлена успешно")
        
        # ШАГ 6: Проверяем, что лид сохранился
        lead = ContactForm.objects.filter(phone='+998901234567').first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.name, 'Интеграционный Тест')
        print("✅ Лид сохранен в БД")
        
        # ШАГ 7: Проверяем языковые версии
        print("\n📍 ШАГ 5: Языковые версии")
        for lang in ['/', '/ru/', '/en/']:
            response = self.client.get(lang)
            self.assertEqual(response.status_code, 200)
            print(f"✅ {lang} - работает")
        
        print("\n" + "="*60)
        print("🎉 ВСЕ ШАГИ ПРОЙДЕНЫ УСПЕШНО!")
        print("="*60)