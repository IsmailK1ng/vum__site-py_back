"""
⚡ ТЕСТЫ НАГРУЗКИ
"""
from django.test import TestCase, Client
import time


class LoadTest(TestCase):
    """Проверка производительности под нагрузкой"""
    
    def setUp(self):
        self.client = Client()
    
    def test_multiple_requests_performance(self):
        """Проверка скорости при множественных запросах"""
        print("\n⚡ ТЕСТ: Множественные запросы")
        
        urls = ['/', '/products/', '/contact/']
        iterations = 10
        
        for url in urls:
            start_time = time.time()
            
            # 10 запросов подряд
            for _ in range(iterations):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
            
            end_time = time.time()
            avg_time = ((end_time - start_time) / iterations) * 1000
            
            print(f"✅ {url}: {avg_time:.2f}ms среднее на запрос")
            
            # Среднее время должно быть < 50ms
            self.assertLess(avg_time, 50)
        
        print("✅ Сайт быстро работает под нагрузкой!")