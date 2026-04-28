import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from asgiref.sync import sync_to_async

from main.models import TelegramUser
from main.services.telegram.bot_service import BotService
from main.services.telegram.triggers import CONTACTS_TRIGGERS

logger = logging.getLogger('bot')
router = Router(name='contacts')


@sync_to_async
def _get_contacts():
    return BotService.get_contacts()


@sync_to_async
def _get_contacts_texts(lang: str) -> dict:
    keys = [
        'contacts_title',
        'contacts_phone',
        'contacts_phone_alt',
        'contacts_email',
        'contacts_address',
        'contacts_hours',
        'contacts_map',
    ]
    return BotService.get_messages_bulk(keys, lang)


def _build_contacts_keyboard(contacts, map_label: str) -> InlineKeyboardMarkup:
    rows = []

    if contacts.map_url:
        rows.append([InlineKeyboardButton(text=map_label, url=contacts.map_url)])

    if contacts.website:
        rows.append([InlineKeyboardButton(text='faw.uz', url=contacts.website)])

    social_row = []
    if contacts.telegram_channel:
        social_row.append(InlineKeyboardButton(
            text='Telegram', url=contacts.telegram_channel,
        ))
    if contacts.instagram:
        social_row.append(InlineKeyboardButton(
            text='Instagram', url=contacts.instagram,
        ))
    if social_row:
        rows.append(social_row)

    social_row2 = []
    if contacts.youtube:
        social_row2.append(InlineKeyboardButton(
            text='YouTube', url=contacts.youtube,
        ))
    if contacts.facebook:
        social_row2.append(InlineKeyboardButton(
            text='Facebook', url=contacts.facebook,
        ))
    if social_row2:
        rows.append(social_row2)

    if contacts.linkedin:
        rows.append([InlineKeyboardButton(text='LinkedIn', url=contacts.linkedin)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_contacts_text(contacts, texts: dict, lang: str) -> str:
    address = getattr(contacts, f'address_{lang}', None) or contacts.address_ru
    hours = getattr(contacts, f'working_hours_{lang}', None) or contacts.working_hours_ru

    lines = [texts.get('contacts_title', ''), '']
    lines.append(texts.get('contacts_phone', '{phone}').format(phone=contacts.phone_main))

    if contacts.phone_secondary:
        lines.append(
            texts.get('contacts_phone_alt', '{phone}').format(phone=contacts.phone_secondary)
        )

    lines.append(texts.get('contacts_email', '{email}').format(email=contacts.email))
    lines.append(texts.get('contacts_address', '{address}').format(address=address))
    lines.append(texts.get('contacts_hours', '{hours}').format(hours=hours))

    return '\n'.join(lines)


@router.message(StateFilter('*'), F.text.in_(CONTACTS_TRIGGERS))
async def handle_contacts(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()

    contacts = await _get_contacts()
    texts = await _get_contacts_texts(lang)
    text = _build_contacts_text(contacts, texts, lang)
    keyboard = _build_contacts_keyboard(contacts, texts.get('contacts_map', 'Map'))

    await message.answer(text, reply_markup=keyboard)
    logger.info('Contacts viewed: telegram_id=%s', message.from_user.id)