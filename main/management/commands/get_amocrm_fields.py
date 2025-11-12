# main/management/commands/get_amocrm_fields.py

from django.core.management.base import BaseCommand
from main.services.amocrm.token_manager import TokenManager
from main.services.amocrm.client import AmoCRMClient


class Command(BaseCommand):
    help = 'Получить список всех кастомных полей в amoCRM'

    def handle(self, *args, **options):
        try:
            access_token = TokenManager.get_valid_token()
            client = AmoCRMClient(access_token)
            
            fields = client.get_custom_fields('leads')
            
            self.stdout.write("\n" + "="*60)
            self.stdout.write("КАСТОМНЫЕ ПОЛЯ ЛИДОВ В amoCRM:")
            self.stdout.write("="*60)
            
            for field in fields:
                field_id = field['id']
                field_name = field['name']
                field_type = field['type']
                
                self.stdout.write(f"\nID: {field_id}")
                self.stdout.write(f"Название: {field_name}")
                self.stdout.write(f"Тип: {field_type}")
                self.stdout.write("-" * 60)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка: {str(e)}"))