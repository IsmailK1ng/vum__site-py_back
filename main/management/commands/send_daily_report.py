from django.core.management.base import BaseCommand
from main.services.telegram.report_sender import TelegramReportSender


class Command(BaseCommand):
    help = 'Отправить ежедневный отчёт в Telegram'

    def handle(self, *args, **options):
        self.stdout.write("📊 Формирование ежедневного отчёта...")
        TelegramReportSender.send_daily_report()
        self.stdout.write(self.style.SUCCESS("✅ Отчёт отправлен!"))