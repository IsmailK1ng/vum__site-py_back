import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from asgiref.sync import sync_to_async

from main.models import TelegramUser
from main.services.telegram.bot_service import BotService, TEST_DRIVE_TIME_SLOTS
from main.services.telegram.keyboards.common import get_button_labels
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.states.fsm import DealerStates, TestDriveStates
from main.services.telegram.triggers import DEALERS_TRIGGERS
from main.services.telegram.utils import get_message

logger = logging.getLogger('bot')
router = Router(name='dealers')

_LABEL_MAP = {
    'address':       {'ru': 'Адрес',       'uz': 'Manzil',    'en': 'Address'},
    'phone':         {'ru': 'Телефон',     'uz': 'Telefon',   'en': 'Phone'},
    'working_hours': {'ru': 'Часы работы', 'uz': 'Ish vaqti', 'en': 'Working hours'},
}

_NO_PRODUCTS_TEXT = {
    'ru': 'Нет доступных моделей для тест-драйва.',
    'uz': "Test-drayv uchun mavjud modellar yo'q.",
    'en': 'No models available for test drive.',
}

_CHOOSE_MODEL_TEXT = {
    'ru': 'Выберите модель для тест-драйва:',
    'uz': 'Test-drayv uchun modelni tanlang:',
    'en': 'Choose a model for the test drive:',
}


# ─── Async обёртки ───────────────────────────────────────────────────────────

@sync_to_async
def _get_dealers(language: str) -> list[dict]:
    return BotService.get_dealers(language)


@sync_to_async
def _get_all_products(language: str) -> list[dict]:
    return BotService.get_all_active_products(language)  # публичный метод


# ─── Форматирование и клавиатуры ─────────────────────────────────────────────

def _format_dealer_card(dealer: dict, language: str) -> str:
    lines = [f"<b>{dealer['name']}</b>"]
    if dealer.get('city'):
        lines.append(dealer['city'])
    for field, labels in _LABEL_MAP.items():
        value = dealer.get(field)
        if not value:
            continue
        if field == 'working_hours':
            value = value.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
        lines.append(f"{labels.get(language, labels['ru'])}: {value}")
    return '\n'.join(lines)


def _build_dealer_inline_keyboard(dealer: dict, language: str) -> InlineKeyboardMarkup:
    map_label = {'ru': 'Открыть на карте',        'uz': 'Xaritada ochish',      'en': 'Open on map'}
    td_label  = {'ru': 'Записаться на тест-драйв', 'uz': 'Test-drayvga yozilish', 'en': 'Book test drive'}
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=map_label.get(language, map_label['ru']),
            url=dealer['map_url'],
        )],
        [InlineKeyboardButton(
            text=td_label.get(language, td_label['ru']),
            callback_data=f"td_from_dealer:{dealer['id']}",
        )],
    ])


def _build_dealers_keyboard(dealers: list[dict], language: str) -> ReplyKeyboardMarkup:
    back_label = get_button_labels(language)['back']
    rows = [[KeyboardButton(text=d['name'])] for d in dealers]
    rows.append([KeyboardButton(text=back_label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _build_products_keyboard(products: list[dict], language: str) -> ReplyKeyboardMarkup:
    back_label = get_button_labels(language)['back']
    rows = [[KeyboardButton(text=p['title'])] for p in products]
    rows.append([KeyboardButton(text=back_label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.in_(DEALERS_TRIGGERS))
async def handle_dealers_enter(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()

    dealers = await _get_dealers(lang)
    if not dealers:
        text = await get_message('dealers_no_dealers', lang)
        await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
        return

    await state.set_state(DealerStates.choose_dealer)
    await state.update_data(language=lang, dealers={d['name']: d for d in dealers})

    text = await get_message('dealers_title', lang)
    await message.answer(text, reply_markup=_build_dealers_keyboard(dealers, lang))


@router.message(DealerStates.choose_dealer)
async def handle_dealer_choice(
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

    dealer = data.get('dealers', {}).get(message.text)
    if not dealer:
        await message.answer(await get_message('choose_from_list', lang))
        return

    await message.answer(
        _format_dealer_card(dealer, lang),
        reply_markup=_build_dealer_inline_keyboard(dealer, lang),
    )
    logger.info(
        'Dealer viewed: telegram_id=%s dealer_id=%s',
        message.from_user.id, dealer['id'],
    )


@router.callback_query(F.data.startswith('td_from_dealer:'))
async def handle_td_from_dealer(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'

    try:
        dealer_id = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        await callback.answer()
        return

    products = await _get_all_products(lang)

    if not products:
        await callback.answer(
            _NO_PRODUCTS_TEXT.get(lang, _NO_PRODUCTS_TEXT['ru']),
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(TestDriveStates.choose_product)
    await state.update_data(
        language=lang,
        td_products={p['title']: p['id'] for p in products},
        td_from_catalog=False,
    )

    await callback.message.answer(
        _CHOOSE_MODEL_TEXT.get(lang, _CHOOSE_MODEL_TEXT['ru']),
        reply_markup=_build_products_keyboard(products, lang),
    )
    await callback.answer()