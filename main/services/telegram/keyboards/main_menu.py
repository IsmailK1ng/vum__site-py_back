from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from asgiref.sync import sync_to_async

from main.services.telegram.bot_service import BotService


@sync_to_async
def _get_menu_items(language: str) -> list[dict]:
    return BotService.get_menu_items(language)


async def get_main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    """
    Главное меню — строится из BotMenuItem в БД.
    Кнопки 2 в ряд для читаемости на маленьком экране.
    """
    items = await _get_menu_items(language)

    rows = []
    row = []
    for item in items:
        row.append(KeyboardButton(text=item['label']))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)