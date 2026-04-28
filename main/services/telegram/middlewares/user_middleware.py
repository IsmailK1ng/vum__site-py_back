import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async

from main.services.telegram.bot_service import BotService

logger = logging.getLogger('bot')


@sync_to_async
def _get_or_create_user(telegram_id: int, **kwargs):
    return BotService.get_or_create_user(telegram_id, **kwargs)


@sync_to_async
def _mark_blocked(telegram_id: int):
    BotService.mark_user_blocked(telegram_id)


class UserMiddleware(BaseMiddleware):
    """
    Middleware — выполняется перед каждым handler.
    Загружает пользователя из БД и кладёт в data['user'].
    Обновляет username если изменился.
    Если пользователь не найден — создаёт с базовыми данными.
    """

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        # Получаем from_user из Message или CallbackQuery
        from_user = event.from_user
        if from_user is None:
            return await handler(event, data)

        try:
            user, created = await _get_or_create_user(
                telegram_id=from_user.id,
                username=from_user.username,
            )
            data['user'] = user
            data['language'] = user.language or 'ru'

            if created:
                logger.info(
                    'New user registered: telegram_id=%s username=%s',
                    from_user.id,
                    from_user.username,
                )

        except Exception as exc:
            logger.error(
                'UserMiddleware error for telegram_id=%s: %s',
                from_user.id,
                exc,
                exc_info=True,
            )
            # Не блокируем работу бота если БД недоступна
            data['user'] = None
            data['language'] = 'ru'

        return await handler(event, data)