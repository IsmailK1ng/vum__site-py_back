import asyncio
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger('bot')


class Command(BaseCommand):
    help = 'Отправить напоминания о тест-драйве на завтра'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Проверить без реальной отправки',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write('DRY RUN — сообщения не отправляются')
        asyncio.run(self._run(dry_run=dry_run))

    async def _run(self, dry_run: bool) -> None:
        from asgiref.sync import sync_to_async
        from datetime import date, timedelta
        from main.models import BotConfig, TestDriveRequest, BotMessage

        @sync_to_async
        def get_config():
            return BotConfig.get_instance()

        @sync_to_async
        def get_tomorrow_requests():
            tomorrow = date.today() + timedelta(days=1)
            return list(
                TestDriveRequest.objects.filter(
                    preferred_date=tomorrow,
                    status__in=['new', 'confirmed'],
                    reminder_sent=False,
                ).select_related('user', 'dealer', 'product')
            )

        @sync_to_async
        def mark_reminder_sent(request_id: int):
            TestDriveRequest.objects.filter(pk=request_id).update(reminder_sent=True)

        @sync_to_async
        def get_reminder_text(lang: str, name: str, date_str: str, time_str: str, dealer_name: str) -> str:
            """Берём текст из BotMessage или используем fallback."""
            try:
                msg = BotMessage.objects.get(key='td_reminder', language=lang)
                return msg.text.format(
                    name=name,
                    date=date_str,
                    time=time_str,
                    dealer=dealer_name,
                )
            except BotMessage.DoesNotExist:
                pass

            templates = {
                'ru': (
                    'Здравствуйте, <b>{name}</b>!\n\n'
                    'Напоминаем: завтра у вас тест-драйв.\n\n'
                    'Дата: <b>{date}</b>\n'
                    'Время: <b>{time}</b>\n'
                    'Дилер: <b>{dealer}</b>\n\n'
                    'Ждём вас!'
                ),
                'uz': (
                    'Salom, <b>{name}</b>!\n\n'
                    'Eslatma: ertaga sizda test-drayv bor.\n\n'
                    'Sana: <b>{date}</b>\n'
                    'Vaqt: <b>{time}</b>\n'
                    'Diler: <b>{dealer}</b>\n\n'
                    'Sizni kutamiz!'
                ),
                'en': (
                    'Hello, <b>{name}</b>!\n\n'
                    'Reminder: you have a test drive tomorrow.\n\n'
                    'Date: <b>{date}</b>\n'
                    'Time: <b>{time}</b>\n'
                    'Dealer: <b>{dealer}</b>\n\n'
                    'We look forward to seeing you!'
                ),
            }
            template = templates.get(lang, templates['ru'])
            return template.format(
                name=name,
                date=date_str,
                time=time_str,
                dealer=dealer_name,
            )

        config = await get_config()
        if not config or not config.bot_token:
            self.stderr.write('BotConfig не настроен — токен отсутствует.')
            return

        requests = await get_tomorrow_requests()

        if not requests:
            self.stdout.write('Нет тест-драйвов на завтра.')
            return

        self.stdout.write(f'Найдено заявок: {len(requests)}')

        if dry_run:
            for td in requests:
                self.stdout.write(
                    f'  DRY RUN: {td.client_name} — '
                    f'{td.preferred_date} {td.preferred_time} — '
                    f'{td.dealer.name if td.dealer else "?"}'
                )
            return

        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
        from main.models import TelegramUser

        bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        sent = failed = skipped = 0

        try:
            for td in requests:
                if not td.user or not td.user.telegram_id:
                    skipped += 1
                    logger.warning('TD reminder skipped — no telegram_id: td_id=%s', td.id)
                    continue

                lang = td.user.language or 'ru'
                name = td.client_name or td.user.first_name or 'Клиент'
                date_str = td.preferred_date.strftime('%d.%m.%Y')
                time_str = td.preferred_time
                dealer_name = td.dealer.name if td.dealer else '—'

                text = await get_reminder_text(lang, name, date_str, time_str, dealer_name)

                try:
                    await bot.send_message(
                        chat_id=td.user.telegram_id,
                        text=text,
                    )
                    await mark_reminder_sent(td.id)
                    sent += 1
                    logger.info('TD reminder sent: td_id=%s telegram_id=%s', td.id, td.user.telegram_id)

                except TelegramForbiddenError:
                    await sync_to_async(
                        TelegramUser.objects.filter(telegram_id=td.user.telegram_id).update
                    )(is_blocked=True)
                    skipped += 1
                    logger.warning('TD reminder blocked: td_id=%s telegram_id=%s', td.id, td.user.telegram_id)

                except TelegramBadRequest as exc:
                    failed += 1
                    logger.error('TD reminder bad request td_id=%s: %s', td.id, exc)

                except Exception as exc:
                    failed += 1
                    logger.error('TD reminder error td_id=%s: %s', td.id, exc)

                await asyncio.sleep(0.05)

        finally:
            await bot.session.close()

        self.stdout.write(
            f'Готово: отправлено={sent} пропущено={skipped} ошибок={failed}'
        )