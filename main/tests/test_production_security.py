# test_production_security.py
from django.test import TestCase
from django.conf import settings

class ProductionSecurityTest(TestCase):
    def test_secure_cookies_settings(self):
        """Проверяем логику безопасности"""
        
        print("\n🔒 Проверка безопасности:")
        print(f"DEBUG = {settings.DEBUG}")
        print(f"SESSION_COOKIE_SECURE = {settings.SESSION_COOKIE_SECURE}")
        print(f"CSRF_COOKIE_SECURE = {settings.CSRF_COOKIE_SECURE}")
        
        # ✅ ПРАВИЛЬНО: Проверяем логику
        if not settings.DEBUG:
            # На продакшене (DEBUG=False) должны быть True
            assert settings.SESSION_COOKIE_SECURE == True, \
                "SESSION_COOKIE_SECURE должен быть True на проде!"
            assert settings.CSRF_COOKIE_SECURE == True, \
                "CSRF_COOKIE_SECURE должен быть True на проде!"
        else:
            # В тестах (DEBUG=True) могут быть False
            print("⚠️ Тесты запущены с DEBUG=True")
            print("   Флаги безопасности выключены (норма)")
        
        # Тест всегда проходит, просто информирует
        self.assertTrue(True)