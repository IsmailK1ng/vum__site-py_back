import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from asgiref.sync import sync_to_async

from main.models import TelegramUser
from main.services.telegram.bot_service import BotService, PRODUCT_SUBCATEGORIES
from main.services.telegram.keyboards.common import BUTTON_LABELS
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.states.fsm import CatalogStates
from main.services.telegram.triggers import CATALOG_TRIGGERS
from main.services.telegram.utils import get_message, get_config, read_file

logger = logging.getLogger('bot')
router = Router(name='catalog')


# ─── Async обёртки ───────────────────────────────────────────────────────────

@sync_to_async
def _get_categories(language: str) -> list[dict]:
    return BotService.get_categories(language)


@sync_to_async
def _get_subcategories_all(language: str) -> list[dict]:
    return BotService.get_subcategories_all(language)


@sync_to_async
def _get_products_by_filter(
    language: str,
    category: str | None = None,
    subcategory: str | None = None,
) -> list[dict]:
    return BotService.get_products_by_filter(language, category, subcategory)


@sync_to_async
def _get_product_detail(product_id: int, language: str) -> dict | None:
    return BotService.get_product_detail(product_id, language)


@sync_to_async
def _record_view(user: TelegramUser, product_id: int) -> None:
    BotService.record_product_view(user, product_id)


@sync_to_async
def _toggle_wishlist(user: TelegramUser, product_id: int) -> bool:
    return BotService.toggle_wishlist(user, product_id)


@sync_to_async
def _create_lead(data: dict):
    return BotService.create_lead(data, utm_campaign='catalog_lead')


@sync_to_async
def _get_product_title(product_id: int, lang: str) -> str:
    return BotService.get_product_title(product_id, lang)


@sync_to_async
def _get_catalog_file_path() -> str | None:
    from main.models import BotConfig
    config = BotConfig.get_instance()
    if config and config.catalog_file:
        try:
            return config.catalog_file.path
        except Exception:
            return None
    return None


# ─── Константы ───────────────────────────────────────────────────────────────

BROWSE_MODE_LABELS = {
    'by_type': {
        'ru': 'По типу кузова',
        'uz': "Kuzov turi bo'yicha",
        'en': 'By body type',
    },
    'by_platform': {
        'ru': 'По модели платформы',
        'uz': "Platforma modeli bo'yicha",
        'en': 'By platform model',
    },
}

_CHOOSE_PLATFORM_TEXT = {
    'ru': 'Выберите платформу:',
    'uz': 'Platformani tanlang:',
    'en': 'Choose platform:',
}

_CHOOSE_CATALOG_TEXT = {
    'ru': 'Как удобнее просматривать каталог?',
    'uz': "Katalogni qanday ko'rishni xohlaysiz?",
    'en': 'How would you like to browse the catalog?',
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

_NOT_REGISTERED = {
    'ru': 'Для заявки нужен номер телефона. Нажмите /start для регистрации.',
    'uz': "Ariza uchun telefon kerak. Ro'yxatdan o'tish uchun /start bosing.",
    'en': 'Phone required. Press /start to register.',
}

_DOWNLOAD_CATALOG_LABEL = {
    'ru': 'Скачать каталог',
    'uz': 'Katalogni yuklab olish',
    'en': 'Download catalog',
}

_CATALOG_FILE_NOT_FOUND = {
    'ru': 'Каталог временно недоступен. Попробуйте позже.',
    'uz': "Katalog vaqtincha mavjud emas. Keyinroq urinib ko'ring.",
    'en': 'Catalog is temporarily unavailable. Please try later.',
}

# Все три варианта для фильтра handler
_ALL_DOWNLOAD_LABELS: frozenset[str] = frozenset(_DOWNLOAD_CATALOG_LABEL.values())


# ─── Вспомогательные функции ─────────────────────────────────────────────────

def _parse_callback_int(data: str) -> int | None:
    try:
        return int(data.split(':')[1])
    except (IndexError, ValueError):
        return None


# ─── Клавиатуры ──────────────────────────────────────────────────────────────

def _build_browse_mode_keyboard(language: str, has_catalog: bool = False) -> ReplyKeyboardMarkup:
    back_label = BUTTON_LABELS[language]['back']
    rows = [
        [KeyboardButton(text=BROWSE_MODE_LABELS['by_type'][language])],
        [KeyboardButton(text=BROWSE_MODE_LABELS['by_platform'][language])],
    ]
    if has_catalog:
        rows.append([KeyboardButton(text=_DOWNLOAD_CATALOG_LABEL[language])])
    rows.append([KeyboardButton(text=back_label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _build_items_keyboard(
    items: list[dict],
    language: str,
    show_count: bool = True,
) -> ReplyKeyboardMarkup:
    back_label = BUTTON_LABELS[language]['back']
    rows = []
    row = []
    for item in items:
        label = (
            f"{item['label']} ({item['count']})"
            if show_count and item.get('count') is not None
            else item['label']
        )
        row.append(KeyboardButton(text=label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=back_label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _build_products_keyboard(products: list[dict], language: str) -> ReplyKeyboardMarkup:
    back_label = BUTTON_LABELS[language]['back']
    rows = [[KeyboardButton(text=p['title'])] for p in products]
    rows.append([KeyboardButton(text=back_label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _build_product_inline_keyboard(
    product: dict,
    language: str,
    site_url: str,
) -> InlineKeyboardMarkup:
    labels = {
        'site':     {'ru': 'Полные характеристики на сайте', 'uz': "To'liq texnik ma'lumotlar",  'en': 'Full specs on website'},
        'price':    {'ru': 'Узнать цену / Заказать звонок',  'uz': "Narxni bilish / Qo'ng'iroq", 'en': 'Get price / Call back'},
        'td':       {'ru': 'Записаться на тест-драйв',       'uz': 'Test-drayvga yozilish',       'en': 'Book test drive'},
        'wishlist': {'ru': 'В избранное',                    'uz': 'Sevimlilarga',                'en': 'Add to favourites'},
    }
    pid = product['id']
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=labels['site'].get(language, labels['site']['ru']),
            url=f"{site_url}/products/{product['slug']}/",
        )],
        [InlineKeyboardButton(
            text=labels['price'].get(language, labels['price']['ru']),
            callback_data=f"lead_from_catalog:{pid}",
        )],
        [InlineKeyboardButton(
            text=labels['td'].get(language, labels['td']['ru']),
            callback_data=f"td_from_catalog:{pid}",
        )],
        [InlineKeyboardButton(
            text=labels['wishlist'].get(language, labels['wishlist']['ru']),
            callback_data=f"wishlist_toggle:{pid}",
        )],
    ])


def _format_product_card(product: dict, language: str) -> str:
    lines = [f"<b>{product['title']}</b>"]

    if product.get('year'):
        year_label = {'ru': 'Год', 'uz': 'Yil', 'en': 'Year'}.get(language, 'Year')
        lines.append(f"{year_label}: {product['year']}")

    if product.get('price'):
        price_label = {'ru': 'Цена', 'uz': 'Narx', 'en': 'Price'}.get(language, 'Price')
        prefix = (
            {'ru': 'от ', 'uz': 'dan ', 'en': 'from '}.get(language, '')
            if product.get('price_is_from')
            else ''
        )
        lines.append(f"{price_label}: {prefix}{product['price']}")

    if product.get('card_specs'):
        lines.append('')
        lines.extend(f"• {s}" for s in product['card_specs'])

    if product.get('features'):
        feat_label = {
            'ru': 'Комплектация',
            'uz': 'Komplektatsiya',
            'en': 'Equipment',
        }.get(language, 'Equipment')
        lines.append('')
        lines.append(f"<b>{feat_label}:</b>")
        lines.extend(f"• {f}" for f in product['features'])

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# СКАЧАТЬ КАТАЛОГ — перехватывает из любого состояния
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.in_(_ALL_DOWNLOAD_LABELS))
async def handle_download_catalog(
    message: Message,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    file_path = await _get_catalog_file_path()

    if not file_path:
        await message.answer(_CATALOG_FILE_NOT_FOUND.get(lang, _CATALOG_FILE_NOT_FOUND['ru']))
        return

    try:
        pdf_bytes = await read_file(file_path)
        await message.answer_document(
            document=BufferedInputFile(pdf_bytes, filename='VUM_catalog.pdf'),
        )
        logger.info('Catalog PDF sent: telegram_id=%s', message.from_user.id)
    except Exception as exc:
        logger.error('Catalog PDF send failed: telegram_id=%s error=%s', message.from_user.id, exc)
        await message.answer(_CATALOG_FILE_NOT_FOUND.get(lang, _CATALOG_FILE_NOT_FOUND['ru']))


# ═══════════════════════════════════════════════════════════════════════════════
# ВХОД В КАТАЛОГ
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.in_(CATALOG_TRIGGERS))
async def handle_catalog_enter(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()

    config = await get_config()
    has_catalog = bool(config and config.catalog_file)

    await state.set_state(CatalogStates.choose_browse_mode)
    await state.update_data(language=lang, has_catalog=has_catalog)
    await message.answer(
        _CHOOSE_CATALOG_TEXT.get(lang, _CHOOSE_CATALOG_TEXT['ru']),
        reply_markup=_build_browse_mode_keyboard(lang, has_catalog=has_catalog),
    )


@router.message(CatalogStates.choose_browse_mode)
async def handle_browse_mode(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        await state.clear()
        text = await get_message('main_menu_text', lang)
        await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
        return

    by_type_label     = BROWSE_MODE_LABELS['by_type'][lang]
    by_platform_label = BROWSE_MODE_LABELS['by_platform'][lang]

    if message.text == by_type_label:
        categories = await _get_categories(lang)
        await state.set_state(CatalogStates.choose_category)
        await state.update_data(browse_mode='by_type')
        text = await get_message('catalog_choose_category', lang)
        await message.answer(text, reply_markup=_build_items_keyboard(categories, lang))

    elif message.text == by_platform_label:
        subcategories = await _get_subcategories_all(lang)
        await state.set_state(CatalogStates.choose_subcategory)
        await state.update_data(browse_mode='by_platform')
        await message.answer(
            _CHOOSE_PLATFORM_TEXT.get(lang, _CHOOSE_PLATFORM_TEXT['ru']),
            reply_markup=_build_items_keyboard(subcategories, lang),
        )
    else:
        await message.answer(await get_message('choose_from_list', lang))


@router.message(CatalogStates.choose_category)
async def handle_category_choice(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        data = await state.get_data()
        has_catalog = data.get('has_catalog', False)
        await state.set_state(CatalogStates.choose_browse_mode)
        await message.answer(
            _CHOOSE_CATALOG_TEXT.get(lang, _CHOOSE_CATALOG_TEXT['ru']),
            reply_markup=_build_browse_mode_keyboard(lang, has_catalog=has_catalog),
        )
        return

    raw_text = message.text.split(' (')[0].strip()
    categories = await _get_categories(lang)
    selected = next((c for c in categories if c['label'] == raw_text), None)

    if not selected:
        await message.answer(await get_message('choose_from_list', lang))
        return

    products = await _get_products_by_filter(lang, category=selected['key'])
    if not products:
        await message.answer(await get_message('catalog_no_products', lang))
        return

    await state.set_state(CatalogStates.choose_product)
    await state.update_data(
        selected_category=selected['key'],
        browse_mode='by_type',
        products={p['id']: p['title'] for p in products},
        products_order=[p['id'] for p in products],
    )
    text = await get_message('catalog_choose_product', lang)
    await message.answer(text, reply_markup=_build_products_keyboard(products, lang))


@router.message(CatalogStates.choose_subcategory)
async def handle_subcategory_choice(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        has_catalog = data.get('has_catalog', False)
        await state.set_state(CatalogStates.choose_browse_mode)
        await message.answer(
            _CHOOSE_CATALOG_TEXT.get(lang, _CHOOSE_CATALOG_TEXT['ru']),
            reply_markup=_build_browse_mode_keyboard(lang, has_catalog=has_catalog),
        )
        return

    raw_text = message.text.split(' (')[0].strip()
    selected_sub_key = next(
        (
            k for k, v in PRODUCT_SUBCATEGORIES.items()
            if v.get(lang) == raw_text or v.get('ru') == raw_text
        ),
        None,
    )

    if not selected_sub_key:
        await message.answer(await get_message('choose_from_list', lang))
        return

    products = await _get_products_by_filter(lang, subcategory=selected_sub_key)
    if not products:
        await message.answer(await get_message('catalog_no_products', lang))
        return

    await state.set_state(CatalogStates.choose_product)
    await state.update_data(
        selected_subcategory=selected_sub_key,
        browse_mode='by_platform',
        products={p['id']: p['title'] for p in products},
        products_order=[p['id'] for p in products],
    )
    text = await get_message('catalog_choose_product', lang)
    await message.answer(text, reply_markup=_build_products_keyboard(products, lang))


@router.message(CatalogStates.choose_product)
async def handle_product_choice(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    back_label = BUTTON_LABELS[lang]['back']

    if message.text == back_label:
        has_catalog = data.get('has_catalog', False)
        browse_mode = data.get('browse_mode', 'by_type')
        if browse_mode == 'by_platform':
            subcategories = await _get_subcategories_all(lang)
            await state.set_state(CatalogStates.choose_subcategory)
            await message.answer(
                _CHOOSE_PLATFORM_TEXT.get(lang, _CHOOSE_PLATFORM_TEXT['ru']),
                reply_markup=_build_items_keyboard(subcategories, lang),
            )
        else:
            categories = await _get_categories(lang)
            await state.set_state(CatalogStates.choose_category)
            text = await get_message('catalog_choose_category', lang)
            await message.answer(text, reply_markup=_build_items_keyboard(categories, lang))
        return

    products_map = data.get('products', {})
    product_id = next(
        (pid for pid, title in products_map.items() if title == message.text),
        None,
    )

    if not product_id:
        await message.answer(await get_message('choose_from_list', lang))
        return

    product = await _get_product_detail(product_id, lang)
    if not product:
        await message.answer(await get_message('catalog_no_products', lang))
        return

    if user:
        await _record_view(user, product_id)

    config = await get_config()
    site_url = config.site_url if config else 'https://faw.uz'
    caption = _format_product_card(product, lang)
    inline_kb = _build_product_inline_keyboard(product, lang, site_url)

    image_path = product.get('image_path')
    if image_path:
        try:
            photo_bytes = await read_file(image_path)
            await message.answer_photo(
                photo=BufferedInputFile(photo_bytes, filename='product.jpg'),
                caption=caption,
                reply_markup=inline_kb,
            )
            logger.info('Product viewed: telegram_id=%s product_id=%s', message.from_user.id, product_id)
            return
        except Exception as exc:
            logger.warning('Photo send failed product_id=%s: %s', product_id, exc)

    await message.answer(caption, reply_markup=inline_kb)
    logger.info('Product viewed (no photo): telegram_id=%s product_id=%s', message.from_user.id, product_id)


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('wishlist_toggle:'))
async def handle_wishlist_toggle(
    callback: CallbackQuery,
    user: TelegramUser | None,
):
    if not user:
        await callback.answer(_NOT_REGISTERED['ru'], show_alert=True)
        return

    product_id = _parse_callback_int(callback.data)
    if product_id is None:
        await callback.answer()
        return

    lang = user.language or 'ru'
    added = await _toggle_wishlist(user, product_id)
    text = await get_message(
        'catalog_added_wishlist' if added else 'catalog_removed_wishlist',
        lang,
    )
    await callback.answer(text)


@router.callback_query(F.data.startswith('lead_from_catalog:'))
async def handle_lead_from_catalog(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'

    if not user or not user.phone:
        await callback.answer(
            _NOT_REGISTERED.get(lang, _NOT_REGISTERED['ru']),
            show_alert=True,
        )
        return

    product_id = _parse_callback_int(callback.data)
    if product_id is None:
        await callback.answer()
        return

    product_title = await _get_product_title(product_id, lang)
    client_name  = user.first_name or '—'
    client_phone = user.phone

    confirm_templates = {
        'ru': (
            '<b>Заявка на консультацию:</b>\n\n'
            'Интересует: <b>{product}</b>\n'
            'Имя: <b>{name}</b>\n'
            'Телефон: <b>{phone}</b>\n\n'
            'Отправить менеджеру?'
        ),
        'uz': (
            '<b>Maslahat uchun ariza:</b>\n\n'
            'Qiziqish: <b>{product}</b>\n'
            'Ism: <b>{name}</b>\n'
            'Telefon: <b>{phone}</b>\n\n'
            'Menejerga yuborishni xohlaysizmi?'
        ),
        'en': (
            '<b>Consultation request:</b>\n\n'
            'Interested in: <b>{product}</b>\n'
            'Name: <b>{name}</b>\n'
            'Phone: <b>{phone}</b>\n\n'
            'Send to manager?'
        ),
    }
    confirm_text = confirm_templates.get(lang, confirm_templates['ru']).format(
        product=product_title,
        name=client_name,
        phone=client_phone,
    )

    await state.update_data(
        lead_product_id=product_id,
        lead_product_title=product_title,
        lead_client_name=client_name,
        lead_client_phone=client_phone,
        lead_region=user.region or '',
        language=lang,
    )

    yes_label = {'ru': 'Да, отправить', 'uz': 'Ha, yuborish', 'en': 'Yes, send'}.get(lang, 'Да, отправить')
    no_label  = {'ru': 'Отмена',        'uz': 'Bekor qilish', 'en': 'Cancel'}.get(lang, 'Отмена')

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=yes_label, callback_data=f"lead_confirm:{product_id}"),
        InlineKeyboardButton(text=no_label,  callback_data='lead_cancel'),
    ]])

    await callback.message.answer(confirm_text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith('lead_confirm:'))
async def handle_lead_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    data = await state.get_data()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    lead = await _create_lead({
        'name':          data.get('lead_client_name', ''),
        'phone':         data.get('lead_client_phone', ''),
        'region':        data.get('lead_region', ''),
        'product_title': data.get('lead_product_title', ''),
        'message':       '',
    })

    await state.clear()
    main_menu_kb = await get_main_menu_keyboard(lang)

    if lead:
        await callback.message.answer(
            _LEAD_SUCCESS.get(lang, _LEAD_SUCCESS['ru']),
            reply_markup=main_menu_kb,
        )
        logger.info(
            'Catalog lead created: telegram_id=%s product_id=%s lead_id=%s',
            callback.from_user.id,
            data.get('lead_product_id'),
            lead.id,
        )
    else:
        await callback.message.answer(
            _LEAD_ERROR.get(lang, _LEAD_ERROR['ru']),
            reply_markup=main_menu_kb,
        )

    await callback.answer()


@router.callback_query(F.data == 'lead_cancel')
async def handle_lead_cancel(
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
    await callback.answer()
    text = await get_message('main_menu_text', lang)
    await callback.message.answer(
        text,
        reply_markup=await get_main_menu_keyboard(lang),
    )