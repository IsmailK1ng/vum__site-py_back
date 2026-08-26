import logging

from aiogram import Router
from aiogram.types import ChatMemberUpdated
from asgiref.sync import sync_to_async

from main.services.telegram.bot_service import BotService

logger = logging.getLogger('bot')
router = Router(name='group_membership')

_INACTIVE_STATUSES = {'left', 'kicked'}


@sync_to_async
def _upsert_group(chat_id: int, title: str, chat_type: str) -> None:
    BotService.upsert_bot_group(chat_id, title, chat_type)


@sync_to_async
def _deactivate_group(chat_id: int) -> None:
    BotService.deactivate_bot_group(chat_id)


@router.my_chat_member()
async def handle_bot_membership_change(update: ChatMemberUpdated) -> None:
    """
    Telegram присылает это событие, когда меняется статус самого бота
    в чате — добавили, удалили, повысили до админа и т.д. Личные чаты
    сюда тоже залетают (там update.chat.type == 'private'), их пропускаем —
    для рассылок в группы важны только group/supergroup.
    """
    chat = update.chat
    if chat.type not in ('group', 'supergroup'):
        return

    new_status = update.new_chat_member.status

    if new_status in _INACTIVE_STATUSES:
        await _deactivate_group(chat.id)
        logger.info('Bot removed from group chat_id=%s title=%r', chat.id, chat.title)
    else:
        await _upsert_group(chat.id, chat.title, chat.type)
        logger.info('Bot added/active in group chat_id=%s title=%r', chat.id, chat.title)
