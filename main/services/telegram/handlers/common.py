import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from main.models import TelegramUser
from main.services.telegram.keyboards.common import get_language_keyboard
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.triggers import LANGUAGE_TRIGGERS, PROFILE_TRIGGERS
from main.services.telegram.utils import get_message

logger = logging.getLogger('bot')
router = Router(name='common')


@router.message(StateFilter('*'), F.text.in_(LANGUAGE_TRIGGERS))
async def handle_language_menu(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    await state.clear()
    await message.answer(
        'Выберите язык / Tilni tanlang / Choose language:',
        reply_markup=get_language_keyboard(),
    )


@router.message(StateFilter('*'), F.text.in_(PROFILE_TRIGGERS))
async def handle_profile_any_state(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    await state.clear()
    lang = user.language if user else 'ru'

    if not user:
        text = await get_message('main_menu_text', lang)
        await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
        return

    from main.services.telegram.handlers.profile import show_profile
    await show_profile(message, user, lang)


@router.message(StateFilter('*'))
async def handle_unknown(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'

    logger.debug(
        'Unknown message telegram_id=%s text=%r state=%s',
        message.from_user.id,
        message.text,
        await state.get_state(),
    )

    if not message.text:
        text = await get_message('unsupported_message', lang)
        await message.answer(text)
        return

    await state.clear()
    text = await get_message('main_menu_text', lang)
    await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))