# tests/test_csrf.py
from django.test import TestCase, Client
from django.urls import reverse

class CSRFTest(TestCase):
    def test_contact_form_without_csrf(self):
        """Проверяем, действительно ли требуется CSRF"""
        client = Client(enforce_csrf_checks=True)
        
        url = reverse('contact-list')
        data = {
            'name': 'Test User',
            'phone': '+998901234567',
            'region': 'Toshkent shahri'
        }
        
        # Запрос БЕЗ CSRF токена
        response = client.post(
            url, 
            data, 
            content_type='application/json'
        )
        
        print(f"\n📊 Статус: {response.status_code}")
        
        # Если AllowAny() → 201 (успех)
        # Если требует CSRF → 403 (отказ)
        
        if response.status_code == 201:
            print("⚠️ API принимает запросы БЕЗ CSRF!")
        else:
            print("✅ CSRF защита работает")