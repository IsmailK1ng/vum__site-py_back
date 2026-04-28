import logging
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from asgiref.sync import sync_to_async
from django.utils import timezone

from main.models import TelegramUser
from main.services.telegram.bot_service import BotService, TEST_DRIVE_TIME_SLOTS
from main.services.telegram.keyboards.common import BUTTON_LABELS, get_confirm_keyboard
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.states.fsm import TestDriveStates
from main.services.telegram.triggers import TD_TRIGGERS
from main.services.telegram.utils import get_message

logger = logging.getLogger('bot')
router = Router(name='test_drive')

_DATE_RANGE_DAYS = 14

_CITY_PROMPT = {
    'ru': 'Укажите ваш город для записи на тест-драйв:',
    'uz': 'Test-drayv uchun shahringizni tanlang:',
    'en': 'Choose your city for the test drive:',
}

_CITY_BACK_PROMPT = {
    'ru': 'Укажите ваш город:',
    'uz': 'Shahringizni tanlang:',
    'en': 'Choose your city:',
}

_HAS_ACTIVE_TD = {
    'ru': (
        'У вас уже есть активная заявка на тест-драйв.\n\n'
        'Откройте <b>Мой профиль</b> чтобы отменить её и записаться снова.'
    ),
    'uz': (
        'Sizda allaqachon faol test-drayv arizasi bor.\n\n'
        "Uni bekor qilish uchun <b>Mening profilim</b>ni oching."
    ),
    'en': (
        'You already have an active test drive request.\n\n'
        'Open <b>My profile</b> to cancel it and book again.'
    ),
}

_HAS_ACTIVE_TD_PLAIN = {
    'ru': 'У вас уже есть активная заявка. Откройте профиль чтобы отменить.',
    'uz': 'Sizda faol ariza bor. Bekor qilish uchun profilni oching.',
    'en': 'You already have an active request. Open profile to cancel.',
}

_SUCCESS_TD = {
    'ru': 'Вы успешно записаны на тест-драйв. Мы свяжемся с вами для подтверждения.',
    'uz': "Siz test-drayvga muvaffaqiyatli yozildingiz. Tasdiqlash uchun siz bilan bog'lanamiz.",
    'en': 'You have successfully booked a test drive. We will contact you to confirm.',
}

_ERROR_TD = {
    'ru': 'Произошла ошибка. Позвоните нам или попробуйте позже.',
    'uz': "Xatolik yuz berdi. Bizga qo'ng'iroq qiling yoki keyinroq urinib ko'ring.",
    'en': 'An error occurred. Please call us or try again later.',
}


# ─── Async обёртки ───────────────────────────────────────────────────────────

@sync_to_async
def _get_all_products(language: str) -> list[dict]:
    return BotService.get_all_active_products(language)  


@sync_to_async
def _get_cities() -> list[str]:
    return BotService.get_dealer_cities()


@sync_to_async
def _create_td_lead(data: dict):
    return BotService.create_test_drive_lead(data)


@sync_to_async
def _get_product_title(product_id: int, lang: str) -> str:
    return BotService.get_product_title(product_id, lang)


@sync_to_async
def _get_active_td(user: TelegramUser):
    return BotService.get_active_test_drive(user)


# ─── Клавиатуры ──────────────────────────────────────────────────────────────

def _build_list_keyboard(
    items: list[str],
    language: str,
    columns: int = 1,
) -> ReplyKeyboardMarkup:
    back_label = BUTTON_LABELS[language]['back']
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for item in items:
        row.append(KeyboardButton(text=item))
        if len(row) == columns:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=back_label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _build_date_keyboard(language: str) -> ReplyKeyboardMarkup:
    back_label = BUTTON_LABELS[language]['back']
    today = timezone.localdate()
    dates = [
        (today + timedelta(days=i)).strftime('%d.%m.%Y')
        for i in range(1, _DATE_RANGE_DAYS + 1)
    ]
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for d in dates:
        row.append(KeyboardButton(text=d))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=back_label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _is_valid_date(text: str) -> bool:
    try:
        parsed = datetime.strptime(text, '%d.%m.%Y').date()
        today = timezone.localdate()
        return today < parsed <= today + timedelta(days=_DATE_RANGE_DAYS)
    except ValueError:
        return False


def _build_confirm_text(
    data: dict,
    city: str,
    client_name: str,
    client_phone: str,
    lang: str,
) -> str:
    templates = {
        'ru': (
            '<b>Заявка на тест-драйв:</b>\n\n'
            'Модель: <b>{product}</b>\n'
            'Дата: <b>{date}</b>\n'
            'Время: <b>{time}</b>\n'
            'Город: <b>{city}</b>\n'
            'Имя: <b>{name}</b>\n'
            'Телефон: <b>{phone}</b>\n\n'
            'Менеджер свяжется с вами и уточнит детали.\n\n'
            'Всё верно?'
        ),
        'uz': (
            '<b>Test-drayv uchun ariza:</b>\n\n'
            'Model: <b>{product}</b>\n'
            'Sana: <b>{date}</b>\n'
            'Vaqt: <b>{time}</b>\n'
            'Shahar: <b>{city}</b>\n'
            'Ism: <b>{name}</b>\n'
            'Telefon: <b>{phone}</b>\n\n'
            "Menejer siz bilan bog'lanib, tafsilotlarni aniqlashtiradi.\n\n"
            "Hammasi to'g'rimi?"
        ),
        'en': (
            '<b>Test drive request:</b>\n\n'
            'Model: <b>{product}</b>\n'
            'Date: <b>{date}</b>\n'
            'Time: <b>{time}</b>\n'
            'City: <b>{city}</b>\n'
            'Name: <b>{name}</b>\n'
            'Phone: <b>{phone}</b>\n\n'
            'A manager will contact you to confirm details.\n\n'
            'Is everything correct?'
        ),
    }
    return templates.get(lang, templates['ru']).format(
        product=data.get('td_product_name', ''),
        date=data.get('td_date', ''),
        time=data.get('td_time', ''),
        city=city,
        name=client_name or '—',
        phone=client_phone or '—',
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.in_(TD_TRIGGERS))
async def handle_td_enter(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()

    if user:
        active_td = await _get_active_td(user)
        if active_td:
            await message.answer(
                _HAS_ACTIVE_TD.get(lang, _HAS_ACTIVE_TD['ru']),
                reply_markup=await get_main_menu_keyboard(lang),
            )
            return

    products = await _get_all_products(lang)

    if not products:
        text = await get_message('td_no_dealers', lang)
        await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
        return

    await state.set_state(TestDriveStates.choose_product)
    await state.update_data(
        language=lang,
        td_products={p['title']: p['id'] for p in products},
        td_from_catalog=False,
    )

    text = await get_message('td_choose_product', lang)
    await message.answer(
        text,
        reply_markup=_build_list_keyboard([p['title'] for p in products], lang),
    )


@router.message(TestDriveStates.choose_product)
async def handle_td_product(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        await state.clear()
        text = await get_message('main_menu_text', lang)
        await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
        return

    products_map = data.get('td_products', {})
    product_id = products_map.get(message.text)

    if not product_id:
        await message.answer(await get_message('choose_from_list', lang))
        return

    await state.update_data(td_product_id=product_id, td_product_name=message.text)
    await state.set_state(TestDriveStates.choose_date)
    text = await get_message('td_choose_date', lang)
    await message.answer(text, reply_markup=_build_date_keyboard(lang))


@router.message(TestDriveStates.choose_date)
async def handle_td_date(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        if data.get('td_from_catalog', False):
            await state.clear()
            text = await get_message('main_menu_text', lang)
            await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
        else:
            products_map = data.get('td_products', {})
            text = await get_message('td_choose_product', lang)
            await state.set_state(TestDriveStates.choose_product)
            await message.answer(
                text,
                reply_markup=_build_list_keyboard(list(products_map.keys()), lang),
            )
        return

    if not message.text or not _is_valid_date(message.text):
        await message.answer(await get_message('choose_from_list', lang))
        return

    await state.update_data(td_date=message.text)
    await state.set_state(TestDriveStates.choose_time)
    text = await get_message('td_choose_time', lang)
    await message.answer(
        text,
        reply_markup=_build_list_keyboard(TEST_DRIVE_TIME_SLOTS, lang, columns=3),
    )


@router.message(TestDriveStates.choose_time)
async def handle_td_time(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        text = await get_message('td_choose_date', lang)
        await state.set_state(TestDriveStates.choose_date)
        await message.answer(text, reply_markup=_build_date_keyboard(lang))
        return

    if message.text not in TEST_DRIVE_TIME_SLOTS:
        await message.answer(await get_message('choose_from_list', lang))
        return

    await state.update_data(td_time=message.text)
    cities = await _get_cities()
    await state.set_state(TestDriveStates.choose_city)
    await message.answer(
        _CITY_PROMPT.get(lang, _CITY_PROMPT['ru']),
        reply_markup=_build_list_keyboard(cities, lang, columns=2),
    )


@router.message(TestDriveStates.choose_city)
async def handle_td_city(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        text = await get_message('td_choose_time', lang)
        await state.set_state(TestDriveStates.choose_time)
        await message.answer(
            text,
            reply_markup=_build_list_keyboard(TEST_DRIVE_TIME_SLOTS, lang, columns=3),
        )
        return

    cities = await _get_cities()
    if message.text not in cities:
        await message.answer(await get_message('choose_from_list', lang))
        return

    client_name   = (user.first_name or '') if user else ''
    client_phone  = (user.phone or '') if user else ''
    client_region = (user.region or message.text) if user else message.text

    await state.update_data(
        td_city=message.text,
        td_client_name=client_name,
        td_client_phone=client_phone,
        td_client_region=client_region,
    )

    confirm_text = _build_confirm_text(data, message.text, client_name, client_phone, lang)
    await state.set_state(TestDriveStates.confirm)
    await message.answer(confirm_text, reply_markup=get_confirm_keyboard(lang))


@router.message(TestDriveStates.confirm)
async def handle_td_confirm(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    yes_label  = BUTTON_LABELS[lang]['yes']
    no_label   = BUTTON_LABELS[lang]['no']
    back_label = BUTTON_LABELS[lang]['back']

    if message.text in (no_label, back_label):
        cities = await _get_cities()
        await state.set_state(TestDriveStates.choose_city)
        await message.answer(
            _CITY_BACK_PROMPT.get(lang, _CITY_BACK_PROMPT['ru']),
            reply_markup=_build_list_keyboard(cities, lang, columns=2),
        )
        return

    if message.text != yes_label:
        await message.answer(await get_message('choose_from_list', lang))
        return

    lead, error = await _create_td_lead({
        'telegram_id':    message.from_user.id,
        'product_id':     data.get('td_product_id'),
        'product_title':  data.get('td_product_name', ''),
        'name':           data.get('td_client_name', ''),
        'phone':          data.get('td_client_phone', ''),
        'region':         data.get('td_client_region', ''),
        'city':           data.get('td_city', ''),
        'preferred_date': data.get('td_date', ''),
        'preferred_time': data.get('td_time', ''),
    })

    await state.clear()
    main_menu = await get_main_menu_keyboard(lang)

    if error == 'has_active':
        await message.answer(
            _HAS_ACTIVE_TD.get(lang, _HAS_ACTIVE_TD['ru']),
            reply_markup=main_menu,
        )
    elif lead:
        await message.answer(
            _SUCCESS_TD.get(lang, _SUCCESS_TD['ru']),
            reply_markup=main_menu,
        )
        logger.info(
            'TD lead created: lead_id=%s telegram_id=%s',
            lead.id, message.from_user.id,
        )
    else:
        await message.answer(
            _ERROR_TD.get(lang, _ERROR_TD['ru']),
            reply_markup=main_menu,
        )


@router.callback_query(F.data.startswith('td_from_catalog:'))
async def handle_td_from_catalog(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'

    if user:
        active_td = await _get_active_td(user)
        if active_td:
            await callback.answer(
                _HAS_ACTIVE_TD_PLAIN.get(lang, _HAS_ACTIVE_TD_PLAIN['ru'])[:200],
                show_alert=True,
            )
            return

    try:
        product_id = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        await callback.answer()
        return

    product_title = await _get_product_title(product_id, lang)

    await state.clear()
    await state.set_state(TestDriveStates.choose_date)
    await state.update_data(
        language=lang,
        td_product_id=product_id,
        td_product_name=product_title,
        td_from_catalog=True,
    )

    text = await get_message('td_choose_date', lang)
    await callback.message.answer(text, reply_markup=_build_date_keyboard(lang))
    await callback.answer()