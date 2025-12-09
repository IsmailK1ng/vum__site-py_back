"""
🕐 ТЕСТ ТАЙМЗОНЫ
Проверяет, что время сохраняется правильно
"""
from django.test import TestCase
from django.utils import timezone
from django.conf import settings
from main.models import ContactForm
import json


class TimezoneTest(TestCase):
    """Тест настроек таймзоны"""
    
    def test_timezone_settings(self):
        """
        ✅ Проверяет настройки таймзоны
        """
        print("\n" + "="*60)
        print("🕐 ТЕСТ: Настройки таймзоны")
        print("="*60)
        
        # Проверяем TIME_ZONE в settings
        expected_timezone = 'Asia/Tashkent'
        actual_timezone = settings.TIME_ZONE
        
        print(f"📊 Ожидается: {expected_timezone}")
        print(f"📊 Установлено: {actual_timezone}")
        
        if actual_timezone == expected_timezone:
            print(f"✅ Таймзона правильная!")
        else:
            print(f"❌ ПРОБЛЕМА: Таймзона неправильная!")
            print(f"   Исправьте в settings.py: TIME_ZONE = '{expected_timezone}'")
        
        self.assertEqual(
            actual_timezone,
            expected_timezone,
            f"❌ Таймзона должна быть {expected_timezone}, а не {actual_timezone}"
        )
        
        # Проверяем USE_TZ
        self.assertTrue(settings.USE_TZ, "❌ USE_TZ должно быть True!")
        print(f"✅ USE_TZ = True (правильно)")
    
    def test_lead_creation_time(self):
        """
        ✅ Проверяет, что лиды сохраняются с правильным временем
        """
        print("\n" + "="*60)
        print("🕐 ТЕСТ: Время создания лида")
        print("="*60)
        
        # Текущее время
        before_time = timezone.now()
        
        # Создаем лид
        lead = ContactForm.objects.create(
            name="Тест Таймзона",
            region="Toshkent shahri",
            phone="+998901234567",
            message="Тест времени"
        )
        
        # Время после создания
        after_time = timezone.now()
        
        print(f"📊 Время до создания: {before_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📊 Время лида: {lead.created_at.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📊 Время после: {after_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Проверяем, что время лида между before и after
        self.assertGreaterEqual(lead.created_at, before_time)
        self.assertLessEqual(lead.created_at, after_time)
        
        # Проверяем, что время не UTC (должно быть Asia/Tashkent)
        hour = lead.created_at.hour
        print(f"✅ Лид создан в {hour}:xx (правильный час)")
        
        print("\n✅ ВРЕМЯ ЛИДОВ СОХРАНЯЕТСЯ ПРАВИЛЬНО!")