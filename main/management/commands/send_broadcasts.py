import asyncio
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger('bot')


class Command(BaseCommand):
    help = 'Отправить запланированные рассылки пользователям бота'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Проверить без реальной отправки — показать кол-во получателей',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write('DRY RUN — сообщения не отправляются')
        asyncio.run(self._run(dry_run=dry_run))

    async def _run(self, dry_run: bool) -> None:
        from asgiref.sync import sync_to_async
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode

        from main.services.telegram.bot_service import BotService
        from main.services.telegram.broadcast_sender import send_broadcast, get_recipients, get_group_chat_ids

        get_pending = sync_to_async(BotService.get_pending_broadcasts)
        get_config = sync_to_async(BotService.get_config)

        broadcasts = list(await get_pending())

        if not broadcasts:
            self.stdout.write('Нет запланированных рассылок.')
            return

        config = await get_config()
        if not config or not config.bot_token:
            self.stderr.write('BotConfig не настроен — токен отсутствует.')
            return

        if dry_run:
            for broadcast in broadcasts:
                recipients = await get_recipients(broadcast)
                groups = await get_group_chat_ids(broadcast)
                self.stdout.write(
                    f'Рассылка #{broadcast.pk}: {broadcast.title} — '
                    f'получателей: {len(recipients)}, групп: {len(groups)} '
                    f'(DRY RUN, не отправляем)'
                )
            return

        bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        try:
            for broadcast in broadcasts:
                self.stdout.write(f'Рассылка #{broadcast.pk}: {broadcast.title}')
                try:
                    stats = await send_broadcast(bot, broadcast)
                except Exception as exc:
                    logger.error('send_broadcasts: broadcast#%s failed: %s', broadcast.pk, exc)
                    self.stderr.write(f'  Ошибка: {exc}')
                    continue

                self.stdout.write(
                    f'  Получателей: {stats["total"]} | '
                    f'отправлено={stats["sent"]} ошибок={stats["failed"]} '
                    f'заблокировали={stats["blocked"]}'
                )
        finally:
            await bot.session.close()
