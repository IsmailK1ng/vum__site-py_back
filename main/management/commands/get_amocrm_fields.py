# main/management/commands/get_amocrm_fields.py

from django.core.management.base import BaseCommand
from main.services.amocrm.token_manager import TokenManager
import requests
from django.conf import settings


class Command(BaseCommand):
    help = 'Получить список всех кастомных полей в amoCRM'

    def handle(self, *args, **options):
        try:
            access_token = TokenManager.get_valid_token()
            
            # Прямой запрос вместо AmoCRMClient
            url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/custom_fields"
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            fields = response.json().get('_embedded', {}).get('custom_fields', [])
            
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