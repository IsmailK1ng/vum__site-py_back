"""
📁 ТЕСТ СТАТИЧЕСКИХ ФАЙЛОВ
Проверяет, что статика настроена правильно
"""
from django.test import TestCase, Client
from django.conf import settings
import os


class StaticFilesTest(TestCase):
    """Тест статических файлов"""
    
    def setUp(self):
        self.client = Client()
    
    def test_static_settings(self):
        """
        ✅ Проверяет настройки статики
        """
        print("\n" + "="*60)
        print("📁 ТЕСТ: Настройки статики")
        print("="*60)
        
        print(f"📊 STATIC_URL: {settings.STATIC_URL}")
        print(f"📊 STATIC_ROOT: {settings.STATIC_ROOT}")
        print(f"📊 STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
        
        # Проверяем, что STATIC_URL установлен
        self.assertTrue(settings.STATIC_URL, "❌ STATIC_URL не установлен!")
        print("✅ STATIC_URL настроен")
        
        # Для прода должен быть STATIC_ROOT
        if settings.DEBUG:
            print("⚠️  DEBUG=True (локальная разработка)")
        else:
            self.assertTrue(settings.STATIC_ROOT, "❌ STATIC_ROOT должен быть настроен для прода!")
            print("✅ STATIC_ROOT настроен")
        
        print("\n✅ НАСТРОЙКИ СТАТИКИ ПРОВЕРЕНЫ!")
    
    def test_css_loads(self):
        """
        ✅ Проверяет, что CSS файлы доступны
        """
        print("\n" + "="*60)
        print("🎨 ТЕСТ: Загрузка CSS")
        print("="*60)
        
        # Проверяем главную страницу
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        html = response.content.decode('utf-8')
        
        # Проверяем наличие CSS ссылок
        has_css = 'main_site.css' in html or 'site_main.css' in html
        
        if has_css:
            print("✅ CSS файлы подключены")
        else:
            print("⚠️  ВНИМАНИЕ: CSS файлы не найдены в HTML")
        
        self.assertTrue(has_css, "❌ CSS файлы не подключены!")
        
        print("\n✅ CSS ФАЙЛЫ ЗАГРУЖАЮТСЯ!")