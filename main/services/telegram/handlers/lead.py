import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from asgiref.sync import sync_to_async

from main.models import TelegramUser
from main.services.telegram.bot_service import BotService
from main.services.telegram.keyboards.common import get_button_labels, get_confirm_keyboard
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.states.fsm import LeadStates
from main.services.telegram.triggers import LEAD_TRIGGERS
from main.services.telegram.utils import get_message

logger = logging.getLogger('bot')
router = Router(name='lead')

INTEREST_OPTIONS = {
    'ru': ['Купить автомобиль', 'Узнать цену', 'Записаться на ТО', 'Другое'],
    'uz': ['Avtomobil sotib olish', 'Narxni bilish', 'TOga yozilish', 'Boshqa'],
    'en': ['Buy a vehicle', 'Get a price', 'Book service', 'Other'],
}

_LEAD_SUCCESS = {
    'ru': 'Заявка отправлена. Менеджер свяжется с вами в ближайшее время.',
    'uz': "Ariza yuborildi. Menejer tez orada siz bilan bog'lanadi.",
    'en': 'Request sent. A manager will contact you shortly.',
}

_LEAD_ERROR = {
    'ru': 'Произошла ошибка. Попробуйте позже или позвоните нам.',
    'uz': "Xatolik yuz berdi. Keyinroq urinib ko'ring yoki bizga qo'ng'iroq qiling.",
    'en': 'An error occurred. Please try again later or call us.',
}

# Шаблон подтверждения — хардкод допустим: динамические данные пользователя
_CONFIRM_TEXT = {
    'ru': (
        '<b>Ваша заявка:</b>\n\n'
        'Интерес: <b>{interest}</b>\n'
        'Имя: <b>{name}</b>\n'
        'Телефон: <b>{phone}</b>\n\n'
        'Отправить заявку?'
    ),
    'uz': (
        '<b>Arizangiz:</b>\n\n'
        'Maqsad: <b>{interest}</b>\n'
        'Ism: <b>{name}</b>\n'
        'Telefon: <b>{phone}</b>\n\n'
        'Ariza yuborish?'
    ),
    'en': (
        '<b>Your request:</b>\n\n'
        'Interest: <b>{interest}</b>\n'
        'Name: <b>{name}</b>\n'
        'Phone: <b>{phone}</b>\n\n'
        'Send request?'
    ),
}


@sync_to_async
def _create_lead(data: dict):
    return BotService.create_lead(data, utm_campaign='bot')


def _build_interest_keyboard(language: str) -> ReplyKeyboardMarkup:
    back_label = get_button_labels(language)['back']
    options = INTEREST_OPTIONS.get(language, INTEREST_OPTIONS['ru'])
    rows = [[KeyboardButton(text=opt)] for opt in options]
    rows.append([KeyboardButton(text=back_label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


@router.message(F.text.in_(LEAD_TRIGGERS))
async def handle_lead_enter(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()
    await state.set_state(LeadStates.choose_interest)
    await state.update_data(language=lang)

    text = await get_message('lead_choose_interest', lang)
    await message.answer(text, reply_markup=_build_interest_keyboard(lang))


@router.message(LeadStates.choose_interest)
async def handle_lead_interest(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = get_button_labels(lang)['back']

    if message.text == back_label:
        await state.clear()
        text = await get_message('main_menu_text', lang)
        await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
        return

    valid_options = INTEREST_OPTIONS.get(lang, INTEREST_OPTIONS['ru'])
    if message.text not in valid_options:
        await message.answer(await get_message('choose_from_list', lang))
        return

    client_name   = ''
    client_phone  = ''
    client_region = ''
    if user:
        client_name   = ' '.join(filter(None, [user.first_name, user.last_name]))
        client_phone  = user.phone or ''
        client_region = user.region or ''

    await state.update_data(
        interest=message.text,
        client_name=client_name,
        client_phone=client_phone,
        client_region=client_region,
    )

    confirm_text = _CONFIRM_TEXT.get(lang, _CONFIRM_TEXT['ru']).format(
        interest=message.text,
        name=client_name or '—',
        phone=client_phone or '—',
    )

    await state.set_state(LeadStates.confirm)
    await message.answer(confirm_text, reply_markup=get_confirm_keyboard(lang))


@router.message(LeadStates.confirm)
async def handle_lead_confirm(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    labels = get_button_labels(lang)
    yes_label  = labels['yes']
    no_label   = labels['no']
    back_label = labels['back']

    if message.text in (no_label, back_label):
        await state.set_state(LeadStates.choose_interest)
        text = await get_message('lead_choose_interest', lang)
        await message.answer(text, reply_markup=_build_interest_keyboard(lang))
        return

    if message.text != yes_label:
        await message.answer(await get_message('choose_from_list', lang))
        return

    lead = await _create_lead({
        'name':          data.get('client_name', ''),
        'phone':         data.get('client_phone', ''),
        'region':        data.get('client_region', ''),
        'message':       data.get('interest', ''),
        'product_title': '',
    })

    await state.clear()
    main_menu = await get_main_menu_keyboard(lang)

    if lead:
        await message.answer(
            _LEAD_SUCCESS.get(lang, _LEAD_SUCCESS['ru']),
            reply_markup=main_menu,
        )
        logger.info(
            'Lead created: telegram_id=%s lead_id=%s',
            message.from_user.id, lead.id,
        )
    else:
        await message.answer(
            _LEAD_ERROR.get(lang, _LEAD_ERROR['ru']),
            reply_markup=main_menu,
        )