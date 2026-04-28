import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from asgiref.sync import sync_to_async

from main.models import TelegramUser
from main.services.telegram.bot_service import BotService
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.triggers import FAQ_TRIGGERS
from main.services.telegram.utils import get_message

logger = logging.getLogger('bot')
router = Router(name='faq')

_BACK_LABEL = {
    'ru': 'Главное меню',
    'uz': 'Asosiy menyu',
    'en': 'Main menu',
}

_NOT_FOUND = {
    'ru': 'Вопрос не найден.',
    'uz': 'Savol topilmadi.',
    'en': 'Question not found.',
}


@sync_to_async
def _get_faq_items(language: str) -> list[dict]:
    return BotService.get_faq_items(language)


def _build_faq_keyboard(items: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        label = item['question'][:60] + '…' if len(item['question']) > 60 else item['question']
        rows.append([InlineKeyboardButton(
            text=label,
            callback_data=f"faq:{item['id']}",
        )])
    rows.append([InlineKeyboardButton(
        text=_BACK_LABEL.get(lang, _BACK_LABEL['ru']),
        callback_data='faq_close',
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(StateFilter('*'), F.text.in_(FAQ_TRIGGERS))
async def handle_faq_enter(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()

    items = await _get_faq_items(lang)

    if not items:
        text = await get_message('faq_empty', lang)
        await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
        return

    await state.update_data(
        language=lang,
        faq_items={str(item['id']): item for item in items},
    )

    text = await get_message('faq_title', lang)
    await message.answer(text, reply_markup=_build_faq_keyboard(items, lang))


@router.callback_query(F.data.startswith('faq:'))
async def handle_faq_answer(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language') or (user.language if user else 'ru')

    try:
        item_id = callback.data.split(':')[1]
    except IndexError:
        await callback.answer()
        return

    faq_map = data.get('faq_items', {})
    item = faq_map.get(item_id)

    if not item:
        items = await _get_faq_items(lang)
        item = next((i for i in items if str(i['id']) == item_id), None)

    if not item:
        await callback.answer(
            _NOT_FOUND.get(lang, _NOT_FOUND['ru']),
            show_alert=True,
        )
        return

    text = f"<b>{item['question']}</b>\n\n{item['answer']}"
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == 'faq_close')
async def handle_faq_close(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    text = await get_message('main_menu_text', lang)
    await callback.message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
    await callback.answer()