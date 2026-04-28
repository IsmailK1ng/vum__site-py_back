import asyncio
import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger('bot')

_SEND_DELAY = 0.05  


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
        from main.models import BotBroadcast, BotConfig
        from asgiref.sync import sync_to_async

        @sync_to_async
        def get_pending_broadcasts():
            from django.db.models import Q
            now = timezone.now()
            return list(
                BotBroadcast.objects.filter(
                    status='scheduled',
                ).filter(
                    Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=now)
                )
            )

        @sync_to_async
        def get_recipients(broadcast):
            from main.models import TelegramUser
            from datetime import timedelta

            qs = TelegramUser.objects.filter(is_blocked=False)

            if broadcast.target == 'ru':
                qs = qs.filter(language='ru')
            elif broadcast.target == 'uz':
                qs = qs.filter(language='uz')
            elif broadcast.target == 'en':
                qs = qs.filter(language='en')
            elif broadcast.target == 'hot':
                qs = qs.filter(status='hot')
            elif broadcast.target == 'vip':
                qs = qs.filter(status='vip')
            elif broadcast.target == 'active_30':
                since = timezone.now() - timedelta(days=30)
                qs = qs.filter(last_active__gte=since)
            elif broadcast.target == 'region':
                if broadcast.target_region:
                    qs = qs.filter(region=broadcast.target_region)

            return list(qs.values('telegram_id', 'language'))

        @sync_to_async
        def mark_sending(broadcast):
            BotBroadcast.objects.filter(pk=broadcast.pk).update(
                status='sending',
                total_recipients=broadcast.total_recipients,
            )

        @sync_to_async
        def mark_done(broadcast, sent, failed, blocked):
            BotBroadcast.objects.filter(pk=broadcast.pk).update(
                status='done',
                sent_count=sent,
                failed_count=failed,
                blocked_count=blocked,
                sent_at=timezone.now(),
            )

        @sync_to_async
        def mark_failed(broadcast):
            BotBroadcast.objects.filter(pk=broadcast.pk).update(status='failed')

        @sync_to_async
        def get_config():
            from main.models import BotConfig
            return BotConfig.get_instance()

        broadcasts = await get_pending_broadcasts()

        if not broadcasts:
            self.stdout.write('Нет запланированных рассылок.')
            return

        config = await get_config()
        if not config or not config.bot_token:
            self.stderr.write('BotConfig не настроен — токен отсутствует.')
            return

        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

        bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        try:
            for broadcast in broadcasts:
                self.stdout.write(f'Рассылка #{broadcast.pk}: {broadcast.title}')

                recipients = await get_recipients(broadcast)
                total = len(recipients)
                broadcast.total_recipients = total

                self.stdout.write(f'  Получателей: {total}')

                if dry_run:
                    self.stdout.write('  DRY RUN — пропускаем отправку')
                    continue

                if not recipients:
                    await mark_done(broadcast, 0, 0, 0)
                    continue

                await mark_sending(broadcast)

                sent = failed = blocked = 0

                for recipient in recipients:
                    telegram_id = recipient['telegram_id']
                    lang = recipient['language'] or 'ru'
                    text = broadcast.get_text(lang)

                    if not text:
                        failed += 1
                        continue

                    reply_markup = None
                    if broadcast.button_text and broadcast.button_url:
                        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text=broadcast.button_text,
                                url=broadcast.button_url,
                            )
                        ]])

                    try:
                        if broadcast.image:
                            await bot.send_photo(
                                chat_id=telegram_id,
                                photo=broadcast.image.url,
                                caption=text,
                                reply_markup=reply_markup,
                            )
                        else:
                            await bot.send_message(
                                chat_id=telegram_id,
                                text=text,
                                reply_markup=reply_markup,
                            )
                        sent += 1

                    except TelegramForbiddenError:
                        blocked += 1
                        from asgiref.sync import sync_to_async
                        @sync_to_async
                        def _mark_blocked(tid):
                            from main.models import TelegramUser
                            TelegramUser.objects.filter(telegram_id=tid).update(is_blocked=True)
                        await _mark_blocked(telegram_id)

                    except TelegramBadRequest as exc:
                        logger.warning('Broadcast bad request telegram_id=%s: %s', telegram_id, exc)
                        failed += 1

                    except Exception as exc:
                        logger.error('Broadcast send error telegram_id=%s: %s', telegram_id, exc)
                        failed += 1

                    await asyncio.sleep(_SEND_DELAY)

                await mark_done(broadcast, sent, failed, blocked)
                self.stdout.write(
                    f'  Готово: отправлено={sent} ошибок={failed} заблокировали={blocked}'
                )

        except Exception as exc:
            logger.error('send_broadcasts crashed: %s', exc)
            self.stderr.write(f'Критическая ошибка: {exc}')
        finally:
            await bot.session.close()