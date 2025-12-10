# tests/test_visitor_uid.py
from django.test import TestCase
from main.serializers import ContactFormSerializer

class VisitorUIDTest(TestCase):
    def test_empty_string(self):
        """Пустая строка должна быть валидной"""
        data = {
            'name': 'Test',
            'phone': '+998901234567',
            'region': 'Toshkent shahri',
            'visitor_uid': ''  # Пустая строка
        }
        
        serializer = ContactFormSerializer(data=data)
        assert serializer.is_valid(), f"Ошибки: {serializer.errors}"
    
    def test_sql_injection(self):
        """SQL инъекция должна быть отклонена"""
        data = {
            'name': 'Test',
            'phone': '+998901234567',
            'region': 'Toshkent shahri',
            'visitor_uid': "'; DROP TABLE--"
        }
        
        serializer = ContactFormSerializer(data=data)
        assert not serializer.is_valid(), "SQL инъекция не отклонена!"