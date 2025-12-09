"""
❌ ТЕСТЫ ОБРАБОТКИ ОШИБОК
"""
from django.test import TestCase, Client


class ErrorHandlingTest(TestCase):
    """Проверка обработки ошибок"""
    
    def setUp(self):
        self.client = Client()
    
    def test_404_page(self):
        """Проверка страницы 404"""
        print("\n❌ ТЕСТ: Страница 404")
        
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        print("✅ 404 страница работает")
    
    def test_api_404(self):
        """Проверка API 404"""
        print("\n❌ ТЕСТ: API 404")
        
        response = self.client.get('/api/uz/products/nonexistent-slug/')
        self.assertEqual(response.status_code, 404)
        print("✅ API возвращает 404 для несуществующих продуктов")