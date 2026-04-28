import logging
import re

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Contact,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,

)
from asgiref.sync import sync_to_async

from main.models import REGION_CHOICES, TelegramUser, REGION_LABELS
from main.services.telegram.bot_service import BotService
from main.services.telegram.keyboards.common import (
    BUTTON_LABELS,
    get_back_keyboard,
    get_confirm_keyboard,
    get_language_keyboard,
    get_phone_keyboard,
    remove_keyboard,
)
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.states.fsm import RegistrationStates
from aiogram.filters import CommandStart, StateFilter
from main.services.telegram.triggers import LANGUAGE_TRIGGERS

logger = logging.getLogger('bot')
router = Router(name='start')


# ─── Async обёртки ───────────────────────────────────────────────────────────

@sync_to_async
def _get_or_create_user(telegram_id: int, **kwargs):
    return BotService.get_or_create_user(telegram_id, **kwargs)


@sync_to_async
def _update_user(telegram_id: int, **kwargs):
    return BotService.update_user(telegram_id, **kwargs)


@sync_to_async
def _is_registration_complete(user: TelegramUser) -> bool:
    return BotService.is_registration_complete(user)


@sync_to_async
def _get_message(key: str, language: str, **kwargs) -> str:
    return BotService.get_message(key, language, **kwargs)


# ─── Валидаторы ──────────────────────────────────────────────────────────────

def _validate_name(text: str) -> bool:
    text = text.strip()
    if len(text) < 2 or len(text) > 50:
        return False
    return bool(re.fullmatch(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ\s\-']{2,50}", text))


def _validate_age(text: str) -> bool:
    return text.strip().isdigit() and 16 <= int(text.strip()) <= 90


def _validate_phone(text: str) -> bool:
    phone = text.strip().replace(' ', '').replace('-', '')
    return bool(re.fullmatch(r'\+998\d{9}', phone))


# ─── Клавиатура регионов ─────────────────────────────────────────────────────

def _get_region_keyboard(language: str) -> ReplyKeyboardMarkup:

    back_label = BUTTON_LABELS[language]['back']
    rows = []
    row = []
    for region_key, _ in REGION_CHOICES:
        translations = REGION_LABELS.get(region_key, {})
        display = translations.get(language) or translations.get('uz', region_key)
        row.append(KeyboardButton(text=display))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=back_label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ─── Language map ─────────────────────────────────────────────────────────────

LANGUAGE_MAP = {
    'Русский': 'ru',
    "O'zbekcha": 'uz',
    'English': 'en',
}


# ═══════════════════════════════════════════════════════════════════════════════
# /start
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(CommandStart())
async def handle_start(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    await state.clear()
    uid = message.from_user.id

    if user is None:
        user, _ = await _get_or_create_user(uid)

    if await _is_registration_complete(user):
        lang = user.language or 'ru'
        welcome_text = await _get_message('welcome_back', lang, name=user.first_name or '')
        keyboard = await get_main_menu_keyboard(lang)
        await message.answer(welcome_text, reply_markup=keyboard)
    else:
        await message.answer(
            'Выберите язык / Tilni tanlang / Choose language:',
            reply_markup=get_language_keyboard(),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Выбор языка
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(StateFilter('*'), F.text.in_(LANGUAGE_MAP.keys()))
async def handle_language_choice(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    uid = message.from_user.id
    lang = LANGUAGE_MAP[message.text]

    await _update_user(uid, language=lang)
    await state.update_data(language=lang)

    if user and await _is_registration_complete(user):
        text = await _get_message('language_changed', lang)
        keyboard = await get_main_menu_keyboard(lang)
        await message.answer(text, reply_markup=keyboard)
        return

    # Начинаем регистрацию — только имя
    text = await _get_message('enter_first_name', lang)
    await state.set_state(RegistrationStates.first_name)
    await message.answer(text, reply_markup=remove_keyboard())


# ═══════════════════════════════════════════════════════════════════════════════
# Имя (единственный текстовый шаг)
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(RegistrationStates.first_name)
async def handle_first_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        await state.clear()
        await message.answer(
            'Выберите язык / Tilni tanlang / Choose language:',
            reply_markup=get_language_keyboard(),
        )
        return

    if not message.text or not _validate_name(message.text):
        text = await _get_message('invalid_name', lang)
        await message.answer(text, reply_markup=get_back_keyboard(lang))
        return

    await state.update_data(first_name=message.text.strip())
    text = await _get_message('enter_age', lang)
    await state.set_state(RegistrationStates.age)
    await message.answer(text, reply_markup=get_back_keyboard(lang))


# ═══════════════════════════════════════════════════════════════════════════════
# Возраст
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(RegistrationStates.age)
async def handle_age(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        await state.set_state(RegistrationStates.first_name)
        text = await _get_message('enter_first_name', lang)
        await message.answer(text, reply_markup=get_back_keyboard(lang))
        return

    if not message.text or not _validate_age(message.text):
        text = await _get_message('invalid_age', lang)
        await message.answer(text, reply_markup=get_back_keyboard(lang))
        return

    await state.update_data(age=int(message.text.strip()))
    text = await _get_message('choose_region', lang)
    await state.set_state(RegistrationStates.region)
    await message.answer(text, reply_markup=_get_region_keyboard(lang))


# ═══════════════════════════════════════════════════════════════════════════════
# Регион
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(RegistrationStates.region)
async def handle_region(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        await state.set_state(RegistrationStates.age)
        text = await _get_message('enter_age', lang)
        await message.answer(text, reply_markup=get_back_keyboard(lang))
        return

    region_key = None
    for key, _ in REGION_CHOICES:
        translations = REGION_LABELS.get(key, {})
        if message.text in translations.values():
            region_key = key
            break

    if not region_key:
        text = await _get_message('choose_from_list', lang)
        await message.answer(text, reply_markup=_get_region_keyboard(lang))
        return

    await state.update_data(region=region_key)
    text = await _get_message('enter_phone', lang)
    await state.set_state(RegistrationStates.phone)
    await message.answer(text, reply_markup=get_phone_keyboard(lang))


# ═══════════════════════════════════════════════════════════════════════════════
# Телефон через contact кнопку
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(RegistrationStates.phone, F.contact)
async def handle_phone_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    if message.contact.user_id != message.from_user.id:
        text = await _get_message('phone_own_only', lang)
        await message.answer(text, reply_markup=get_phone_keyboard(lang))
        return

    await _finish_registration(message, state, message.contact.phone_number, lang)


# ═══════════════════════════════════════════════════════════════════════════════
# Телефон ручной ввод
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(RegistrationStates.phone, F.text)
async def handle_phone_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']
    manual_label = BUTTON_LABELS[lang]['enter_phone_manually']

    if message.text == back_label:
        await state.set_state(RegistrationStates.region)
        text = await _get_message('choose_region', lang)
        await message.answer(text, reply_markup=_get_region_keyboard(lang))
        return

    if message.text == manual_label:
        text = await _get_message('enter_phone_manually_hint', lang)
        await message.answer(text, reply_markup=get_back_keyboard(lang))
        return

    if not _validate_phone(message.text):
        text = await _get_message('invalid_phone', lang)
        await message.answer(text, reply_markup=get_phone_keyboard(lang))
        return

    phone = message.text.strip().replace(' ', '').replace('-', '')
    await _finish_registration(message, state, phone, lang)


async def _finish_registration(
    message: Message,
    state: FSMContext,
    phone: str,
    lang: str,
) -> None:
    data = await state.get_data()
    uid = message.from_user.id

    await _update_user(
        uid,
        first_name=data.get('first_name', ''),
        age=data.get('age'),
        region=data.get('region', ''),
        phone=phone,
        language=lang,
    )

    await state.clear()

    first_name = data.get('first_name', '')
    success_text = await _get_message('registration_complete', lang, name=first_name)
    keyboard = await get_main_menu_keyboard(lang)
    await message.answer(success_text, reply_markup=keyboard)

    logger.info(
        'Registration complete: telegram_id=%s lang=%s',
        uid, lang,
    )