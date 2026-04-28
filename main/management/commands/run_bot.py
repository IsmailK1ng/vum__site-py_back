
import asyncio
import logging
import signal

from django.core.management.base import BaseCommand

logger = logging.getLogger('bot')


class Command(BaseCommand):
    help = 'Запуск Telegram бота FAW.UZ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--webhook',
            action='store_true',
            default=False,
            help='Запустить в режиме webhook (по умолчанию polling)',
        )

    def handle(self, *args, **options):
        use_webhook = options['webhook']
        mode = 'webhook' if use_webhook else 'polling'
        self.stdout.write(f'Starting FAW bot in {mode} mode...')
        logger.info('Starting FAW bot in %s mode', mode)

        try:
            asyncio.run(self._run(use_webhook))
        except KeyboardInterrupt:
            self.stdout.write('Bot stopped.')
            logger.info('Bot stopped by user')
        except Exception as exc:
            logger.critical('Bot crashed: %s', exc, exc_info=True)
            raise

    async def _run(self, use_webhook: bool) -> None:
        from main.services.telegram.loader import create_bot_and_dispatcher

        # create_bot_and_dispatcher теперь async — await обязателен
        bot, dp = await create_bot_and_dispatcher()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(self._shutdown(bot, dp)),
                )
            except NotImplementedError:
                # Windows не поддерживает add_signal_handler
                pass

        try:
            if use_webhook:
                await self._start_webhook(bot, dp)
            else:
                await self._start_polling(bot, dp)
        finally:
            await bot.session.close()
            logger.info('Bot session closed')

    @staticmethod
    async def _start_polling(bot, dp) -> None:
        logger.info('Starting polling...')
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, handle_signals=False)

    @staticmethod
    async def _start_webhook(bot, dp) -> None:
        from aiogram.webhook.aiohttp_server import (
            SimpleRequestHandler,
            setup_application,
        )
        from aiohttp import web
        from asgiref.sync import sync_to_async
        from main.services.telegram.bot_service import BotService

        get_config = sync_to_async(BotService.get_config)
        config = await get_config()

        if not config.webhook_url:
            raise ValueError(
                'BotConfig.webhook_url не задан. '
                'Django Admin -> Бот -> Конфигурация -> Webhook URL.'
            )

        webhook_path = '/bot/webhook/'
        await bot.set_webhook(
            url=config.webhook_url,
            allowed_updates=dp.resolve_used_update_types(),
        )
        logger.info('Webhook set to %s', config.webhook_url)

        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=8001)
        await site.start()
        logger.info('Webhook server started on port 8001')

        await asyncio.Event().wait()

    @staticmethod
    async def _shutdown(bot, dp) -> None:
        logger.info('Shutting down bot...')
        await dp.stop_polling()
        await bot.session.close()