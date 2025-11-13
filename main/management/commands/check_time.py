# main/management/commands/check_time.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import AmoCRMToken
import requests
from django.conf import settings


class Command(BaseCommand):
    help = 'Проверить синхронизацию времени Django с amoCRM'

    def handle(self, *args, **options):
        # 1. Время Django
        django_time = timezone.now()
        self.stdout.write(f"🐍 Django время: {django_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # 2. Время токена
        token_obj = AmoCRMToken.get_instance()
        self.stdout.write(f"⏰ Токен истекает: {token_obj.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 3. Время amoCRM (через API)
        try:
            url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/account"
            headers = {'Authorization': f'Bearer {token_obj.access_token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # amoCRM возвращает Unix timestamp в заголовках
            server_time = response.headers.get('Date')
            self.stdout.write(f"☁️  amoCRM время: {server_time}")
            
            self.stdout.write(self.style.SUCCESS("\n✅ Проверка завершена!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка: {str(e)}"))