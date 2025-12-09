from django.test import TestCase
from rest_framework.test import APIClient

class LanguageDetectionTest(TestCase):
    """Проверка определения языка в API"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_uz_endpoint_works(self):
        """Узбекский endpoint работает"""
        response = self.client.get('/api/uz/products/')
        self.assertEqual(response.status_code, 200)
    
    def test_ru_endpoint_works(self):
        """Русский endpoint работает"""
        response = self.client.get('/api/ru/products/')
        self.assertEqual(response.status_code, 200)
    
    def test_en_endpoint_works(self):
        """Английский endpoint работает"""
        response = self.client.get('/api/en/products/')
        self.assertEqual(response.status_code, 200)