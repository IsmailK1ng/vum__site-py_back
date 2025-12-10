# tests/test_race_condition.py
import threading
from django.test import TransactionTestCase
from main.models import Product, ProductFeature, FeatureIcon

class RaceConditionTest(TransactionTestCase):
    def test_concurrent_feature_creation(self):
        """Проверяем race condition при создании features"""
        product = Product.objects.create(
            title="Test Truck",
            slug="test-truck",
            category="samosval",
            main_image="test.jpg"
        )
        
        results = []
        errors = []
        
        def create_feature(name):
            try:
                icon = FeatureIcon.objects.create(
                    name=f"Icon {name}",
                    icon="test.svg"
                )
                feature = ProductFeature.objects.create(
                    product=product,
                    icon=icon,
                    name=name
                )
                results.append(feature.order)
            except Exception as e:
                errors.append(str(e))
        
        # Создаем 10 features одновременно
        threads = [
            threading.Thread(target=create_feature, args=(f"Feature {i}",))
            for i in range(10)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        print(f"\n📊 Результаты order: {sorted(results)}")
        print(f"❌ Ошибки: {errors}")
        
        # Проверяем уникальность
        unique_orders = len(set(results))
        total_orders = len(results)
        
        assert unique_orders == total_orders, \
            f"❌ Дубликаты order! Уникальных: {unique_orders}, Всего: {total_orders}"