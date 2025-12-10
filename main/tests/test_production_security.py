# tests/test_production_security.py
from django.test import TestCase, override_settings
from django.conf import settings

class ProductionSecurityTest(TestCase):
    @override_settings(DEBUG=False)
    def test_secure_cookies_on_production(self):
        """Проверяем безопасность cookies на продакшене"""
        
        # Временно меняем DEBUG
        with self.settings(DEBUG=False):
            # Проверяем настройки
            from django.conf import settings
            
            checks = {
                'SESSION_COOKIE_SECURE': settings.SESSION_COOKIE_SECURE,
                'CSRF_COOKIE_SECURE': settings.CSRF_COOKIE_SECURE,
                'SECURE_SSL_REDIRECT': settings.SECURE_SSL_REDIRECT,
            }
            
            print("\n🔒 Проверка безопасности на продакшене:")
            for name, value in checks.items():
                status = "✅" if value else "❌"
                print(f"{status} {name} = {value}")
            
            assert all(checks.values()), "Не все флаги безопасности включены!"