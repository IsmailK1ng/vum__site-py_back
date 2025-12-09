# main/tests/test_seo.py

from django.test import TestCase, Client
from main.models import Product

class SEOTest(TestCase):
    """Тесты для SEO оптимизации"""
    
    def setUp(self):
        self.client = Client()
        
        # Создаем тестовый продукт
        self.product = Product.objects.create(
            title_uz="Test UZ",
            title_ru="Test RU",
            title_en="Test EN",
            slug="test-product",
            category="tiger_vh",
            is_active=True
        )
    
    def test_hreflang_tags_on_homepage(self):
        """
        ✅ Главная страница содержит hreflang теги
        """
        response = self.client.get('/')
        html = response.content.decode('utf-8')
        
        # Проверяем наличие тегов
        self.assertIn('rel="alternate" hreflang="uz"', html)
        self.assertIn('rel="alternate" hreflang="ru"', html)
        self.assertIn('rel="alternate" hreflang="en"', html)
        self.assertIn('rel="alternate" hreflang="x-default"', html)
        
        # Проверяем правильность URL
        self.assertIn('href="http://testserver/"', html)  # uz (дефолтный)
        self.assertIn('href="http://testserver/ru/"', html)
        self.assertIn('href="http://testserver/en/"', html)
        
        print("✅ Главная страница: hreflang теги присутствуют")
    
    def test_hreflang_tags_on_product_detail(self):
        """
        ✅ Страница продукта содержит hreflang теги
        """
        response = self.client.get(f'/products/{self.product.slug}/')
        html = response.content.decode('utf-8')
        
        # Проверяем наличие тегов
        self.assertIn('rel="alternate" hreflang="uz"', html)
        self.assertIn('rel="alternate" hreflang="ru"', html)
        self.assertIn('rel="alternate" hreflang="en"', html)
        
        # Проверяем правильность URL с slug
        self.assertIn(f'href="http://testserver/products/{self.product.slug}/"', html)
        self.assertIn(f'href="http://testserver/ru/products/{self.product.slug}/"', html)
        self.assertIn(f'href="http://testserver/en/products/{self.product.slug}/"', html)
        
        print("✅ Страница продукта: hreflang теги присутствуют")
    
    def test_canonical_url_matches_current_language(self):
        """
        ✅ Canonical URL соответствует текущему языку
        """
        # Узбекский
        response_uz = self.client.get('/')
        html_uz = response_uz.content.decode('utf-8')
        
        # Должен быть canonical на узбекскую версию
        self.assertIn('rel="canonical" href="http://testserver/"', html_uz)
        
        # Русский
        response_ru = self.client.get('/ru/')
        html_ru = response_ru.content.decode('utf-8')
        
        # Должен быть canonical на русскую версию
        self.assertIn('rel="canonical" href="http://testserver/ru/"', html_ru)
        
        print("✅ Canonical URL правильный для каждого языка")