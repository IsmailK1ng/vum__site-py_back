import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from asgiref.sync import sync_to_async

logger = logging.getLogger('bot')


@sync_to_async
def _load_config():
    from main.services.telegram.bot_service import BotService
    return BotService.get_config()


async def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    from main.services.telegram.middlewares.user_middleware import UserMiddleware
    from main.services.telegram.fsm_storage import DatabaseStorage

    config = await _load_config()

    if not config.bot_token:
        raise ValueError(
            'BotConfig.bot_token не задан. '
            'Django Admin -> Бот -> Конфигурация.'
        )

    if not config.is_active:
        raise ValueError(
            'Бот выключен. '
            'Django Admin -> Бот -> Конфигурация -> Бот активен.'
        )

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = DatabaseStorage()

    dp = Dispatcher(storage=storage)

    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    _register_handlers(dp)

    logger.info('Bot initialized successfully')
    return bot, dp


def _register_handlers(dp: Dispatcher) -> None:
    from main.services.telegram.handlers import (
        start, catalog, dealers, test_drive,
        lead, faq, profile, news, leasing, contacts, common,
    )

    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(dealers.router)
    dp.include_router(test_drive.router)
    dp.include_router(lead.router)
    dp.include_router(faq.router)
    dp.include_router(profile.router)
    dp.include_router(news.router)
    dp.include_router(leasing.router)
    dp.include_router(contacts.router)
    dp.include_router(common.router)

    logger.info('All handlers registered')