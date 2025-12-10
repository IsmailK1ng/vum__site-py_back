# tests/test_categories.py
from django.test import TestCase
from main.models import Product

class CategoriesTest(TestCase):
    def test_false_positive_filtering(self):
        """Проверяем ложные срабатывания __contains"""
        
        # Создаем продукт с категорией "maxsus"
        product1 = Product.objects.create(
            title="Truck 1",
            slug="truck-1",
            category="samosval",
            categories="maxsus,furgon",
            main_image="test.jpg"
        )
        
        # Создаем продукт с категорией "maxsus_special"
        product2 = Product.objects.create(
            title="Truck 2",
            slug="truck-2",
            category="samosval",
            categories="maxsus_special",  # Похоже на maxsus!
            main_image="test.jpg"
        )
        
        # Фильтруем по "maxsus"
        from django.db.models import Q
        result = Product.objects.filter(
            Q(category="maxsus") | Q(categories__contains="maxsus")
        )
        
        print(f"\n🔍 Найдено продуктов: {result.count()}")
        for p in result:
            print(f"  - {p.title}: {p.categories}")
        
        # ❌ ПРОБЛЕМА: product2 тоже найдется!
        assert result.count() == 2, "Ложное срабатывание!"