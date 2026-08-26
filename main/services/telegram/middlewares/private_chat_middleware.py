from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class PrivateChatOnlyMiddleware(BaseMiddleware):
    """
    Бот целиком рассчитан на личку: профиль, избранное, FSM-регистрация —
    всё привязано 1:1 к конкретному Telegram-аккаунту (TelegramUser).
    Групповые чаты как источник входящих сообщений не поддерживаются —
    без этого фильтра любое сообщение в группе (включая служебные, вроде
    "бот добавлен в группу", у которых нет .text) долетало до общего
    catch-all хендлера (handlers/common.py::handle_unknown) и получало
    в ответ "Пожалуйста, используйте кнопки меню" — бессмысленно для группы.

    Не путать ни с исходящими уведомлениями о лидах в BotConfig.notify_chat_id
    (шлются напрямую bot.send_message(), эту middleware не проходят), ни с
    my_chat_member-событием, по которому регистрируются группы для рассылок
    (handlers/group_membership.py) — это отдельный тип апдейта, middleware
    dp.message/dp.callback_query на него не распространяется.
    """

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        chat = event.chat if isinstance(event, Message) else getattr(event.message, 'chat', None)

        if chat is not None and chat.type != 'private':
            return None

        return await handler(event, data)
