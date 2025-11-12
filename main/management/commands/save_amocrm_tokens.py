# main/management/commands/save_amocrm_tokens.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from main.models import AmoCRMToken


class Command(BaseCommand):
    help = 'Сохранить токены amoCRM из Postman в БД'

    def handle(self, *args, **options):
        self.stdout.write("📝 Введите токены из Postman:\n")
        
        access_token = input("Access Token: ").strip()
        refresh_token = input("Refresh Token: ").strip()
        
        if not access_token or not refresh_token:
            self.stdout.write(self.style.ERROR("❌ Токены не могут быть пустыми!"))
            return
        
        # Сохраняем
        token_obj = AmoCRMToken.get_instance()
        token_obj.access_token = access_token
        token_obj.refresh_token = refresh_token
        token_obj.expires_at = timezone.now() + timedelta(hours=24)
        token_obj.save()
        
        self.stdout.write(self.style.SUCCESS(
            f"✅ Токены успешно сохранены!\n"
            f"Истекают: {token_obj.expires_at.strftime('%d.%m.%Y %H:%M')}"
        ))