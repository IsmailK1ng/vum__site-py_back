import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from asgiref.sync import sync_to_async

from main.services.telegram.bot_service import BotService

logger = logging.getLogger('bot')


@sync_to_async
def _get_config():
    return BotService.get_config()


@sync_to_async
def _get_message(key: str, language: str) -> str:
    return BotService.get_message(key, language)


class MaintenanceMiddleware(BaseMiddleware):
    """
    Делает BotConfig.is_active реальным kill-switch'ом.

    Раньше is_active читался только один раз при старте процесса
    (loader.py::create_bot_and_dispatcher) — выключение бота в админке
    ничего не меняло, пока процесс не перезапустят руками. Теперь
    каждое сообщение/callback перепроверяет актуальный статус (кеш
    60с, см. BotService.get_config) и, если бот выключен, вместо
    обычной обработки отвечает заглушкой. Стоит перед UserMiddleware,
    чтобы выключенный бот не плодил/не обновлял TelegramUser впустую.
    """

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        try:
            config = await _get_config()
        except Exception:
            logger.error('MaintenanceMiddleware: failed to load BotConfig', exc_info=True)
            return await handler(event, data)

        if config.is_active:
            return await handler(event, data)

        language = (getattr(event.from_user, 'language_code', None) or 'ru')[:2]
        if language not in ('ru', 'uz', 'en'):
            language = 'ru'
        text = await _get_message('bot_disabled', language)

        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
        elif isinstance(event, Message):
            await event.answer(text)

        return None
