import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)
from asgiref.sync import sync_to_async

from main.models import TelegramUser
from main.services.telegram.bot_service import (
    BotService,
    PRODUCT_CATEGORIES,
    PRODUCT_SUBCATEGORIES,
)
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.states.fsm import LeasingStates
from main.services.telegram.utils import get_config
from main.services.telegram.triggers import LEASING_TRIGGERS
from main.services.telegram.utils import get_config, read_file

logger = logging.getLogger('bot')
router = Router(name='leasing')

LEASING_TRIGGERS = {'Лизинг', 'Lizing', 'Leasing'}

_RATES = {24: 0.22, 36: 0.23, 48: 0.26, 60: 0.265}
_DOWN_OPTIONS = [10, 20, 30, 40, 50, 60]
_TERM_OPTIONS = [12, 18, 24, 36, 48, 60]

_MONTHS   = {'ru': 'мес',  'uz': 'oy',   'en': 'mo'}
_CURRENCY = {'ru': 'сум',  'uz': "so'm", 'en': 'UZS'}

_BROWSE_LABELS = {
    'by_type': {
        'ru': '📦 По типу кузова',
        'uz': "📦 Kuzov turi bo'yicha",
        'en': '📦 By body type',
    },
    'by_platform': {
        'ru': '⚙️ По платформе Tiger',
        'uz': '⚙️ Tiger platformasi',
        'en': '⚙️ By Tiger platform',
    },
}

_TEXT = {
    'enter': {
        'ru': (
            '🏦 <b>Лизинговый калькулятор FAW</b>\n\n'
            'Купите технику в рассрочку от 22% годовых.\n'
            'Срок до 60 месяцев. Взнос от 10%.\n\n'
            'Как удобнее выбрать технику?'
        ),
        'uz': (
            '🏦 <b>FAW lizing kalkulatori</b>\n\n'
            "Texnikani yiliga 22% dan bo'lib to'lang.\n"
            "Muddat 60 oygacha. To'lov 10% dan.\n\n"
            'Texnikani qanday tanlaysiz?'
        ),
        'en': (
            '🏦 <b>FAW Leasing Calculator</b>\n\n'
            'Get your truck from 22% per year.\n'
            'Up to 60 months. Down payment from 10%.\n\n'
            'How would you like to browse?'
        ),
    },
    'choose_category': {'ru': '📦 Выберите тип кузова:',    'uz': '📦 Kuzov turini tanlang:',    'en': '📦 Choose body type:'},
    'choose_platform': {'ru': '⚙️ Выберите платформу:',     'uz': '⚙️ Platformani tanlang:',     'en': '⚙️ Choose platform:'},
    'choose_down':     {'ru': '💵 Выберите первоначальный взнос:', 'uz': "💵 Dastlabki to'lovni tanlang:", 'en': '💵 Choose down payment:'},
    'choose_term':     {'ru': '📅 Выберите срок лизинга:',  'uz': '📅 Lizing muddatini tanlang:', 'en': '📅 Choose lease term:'},
    'no_products':     {'ru': '⚠️ Техники с ценами нет. Обратитесь к менеджеру.', 'uz': "⚠️ Narxli texnika yo'q. Menejer bilan bog'laning.", 'en': '⚠️ No priced products. Please contact a manager.'},
    'lead_success':    {'ru': '✅ Заявка на лизинг отправлена! Менеджер свяжется с вами.', 'uz': "✅ Lizing arizasi yuborildi! Menejer bog'lanadi.", 'en': '✅ Leasing request sent! A manager will contact you.'},
    'lead_error':      {'ru': '❌ Ошибка. Попробуйте позже или позвоните нам.', 'uz': "❌ Xatolik. Keyinroq urinib ko'ring.", 'en': '❌ Error. Try again later or call us.'},
    'no_phone':        {'ru': 'Для заявки нужен телефон. Нажмите /start для регистрации.', 'uz': "Ariza uchun telefon kerak. /start bosing.", 'en': 'Phone required. Press /start to register.'},
    'back':            {'ru': '◀️ Назад',           'uz': '◀️ Orqaga',           'en': '◀️ Back'},
    'back_list':       {'ru': '◀️ Назад к списку',  'uz': "◀️ Ro'yxatga qaytish", 'en': '◀️ Back to list'},
    'choose_model':    {'ru': '✅ Выбрать эту модель', 'uz': '✅ Ushbu modelni tanlash', 'en': '✅ Choose this model'},
    'apply':           {'ru': '📞 Оставить заявку',  'uz': '📞 Ariza qoldirish',  'en': '📞 Apply now'},
    'change_params':   {'ru': '🔄 Изменить параметры', 'uz': "🔄 Parametrlarni o'zgartirish", 'en': '🔄 Change params'},
    'details':         {'ru': '🌐 Подробнее',        'uz': '🌐 Batafsil',         'en': '🌐 Details'},
    'new_calc':        {'ru': '🔄 Новый расчёт',     'uz': '🔄 Yangi hisob',      'en': '🔄 New calculation'},
}


# ─── Async обёртки — только через BotService ─────────────────────────────────

@sync_to_async
def _get_products_by_filter(
    language: str,
    category: str | None = None,
    subcategory: str | None = None,
) -> list[dict]:
    return BotService.get_products_with_prices(language, category, subcategory)

@sync_to_async
def _get_categories_with_prices(language: str) -> list[dict]:
    return BotService.get_categories_with_prices(language)

@sync_to_async
def _get_subcategories_with_prices(language: str) -> list[dict]:
    return BotService.get_subcategories_with_prices(language)

@sync_to_async
def _create_lead(data: dict):
    return BotService.create_lead(data, utm_campaign='leasing')


# ─── Калькулятор ─────────────────────────────────────────────────────────────

def _get_rate(term: int) -> float:
    for months in sorted(_RATES):
        if term <= months:
            return _RATES[months]
    return _RATES[60]


def _calculate(price: int, down_pct: int, term: int) -> dict:
    annual_rate  = _get_rate(term)
    down_payment = round(price * down_pct / 100)
    financing    = price - down_payment
    extra        = round(financing * 0.005)
    total        = financing + extra
    mr           = annual_rate / 12
    k            = (mr * (1 + mr) ** term) / ((1 + mr) ** term - 1)
    monthly      = round(total * k)
    return {
        'price':           price,
        'down_payment':    down_payment,
        'down_pct':        down_pct,
        'financing':       total,
        'monthly_payment': monthly,
        'total_payment':   monthly * term,
        'annual_rate':     annual_rate,
        'term':            term,
    }


def _fmt(n: int) -> str:
    return f"{n:,}".replace(',', ' ')


def _read_photo(image_path: str | None) -> bytes | None:
    if not image_path:
        return None
    try:
        with open(image_path, 'rb') as f:
            return f.read()
    except OSError as exc:
        logger.warning('_read_photo failed path=%s: %s', image_path, exc)
        return None


# ─── Клавиатуры ──────────────────────────────────────────────────────────────

def _build_browse_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_BROWSE_LABELS['by_type'].get(lang, _BROWSE_LABELS['by_type']['ru']),
            callback_data='lz_browse:by_type',
        )],
        [InlineKeyboardButton(
            text=_BROWSE_LABELS['by_platform'].get(lang, _BROWSE_LABELS['by_platform']['ru']),
            callback_data='lz_browse:by_platform',
        )],
    ])


def _build_categories_kb(categories: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = []
    row  = []
    for cat in categories:
        row.append(InlineKeyboardButton(
            text=f"{cat['label']} ({cat['count']})",
            callback_data=f"lz_cat:{cat['key']}",
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(
        text=_TEXT['back'].get(lang, _TEXT['back']['ru']),
        callback_data='lz_back:browse',
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_subcategories_kb(subcategories: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(
            text=f"{s['label']} ({s['count']})",
            callback_data=f"lz_sub:{s['key']}",
        )
        for s in subcategories
    ]]
    rows.append([InlineKeyboardButton(
        text=_TEXT['back'].get(lang, _TEXT['back']['ru']),
        callback_data='lz_back:browse',
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_product_card_kb(index: int, total: int, lang: str) -> InlineKeyboardMarkup:
    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton(text='◀️', callback_data=f'lz_nav:{index - 1}'))
    nav_row.append(InlineKeyboardButton(text=f'{index + 1} / {total}', callback_data='lz_noop'))
    if index < total - 1:
        nav_row.append(InlineKeyboardButton(text='▶️', callback_data=f'lz_nav:{index + 1}'))

    return InlineKeyboardMarkup(inline_keyboard=[
        nav_row,
        [InlineKeyboardButton(
            text=_TEXT['choose_model'].get(lang, _TEXT['choose_model']['ru']),
            callback_data=f'lz_select:{index}',
        )],
        [InlineKeyboardButton(
            text=_TEXT['back'].get(lang, _TEXT['back']['ru']),
            callback_data='lz_back:browse',
        )],
    ])


def _build_down_kb(lang: str) -> InlineKeyboardMarkup:
    row1 = [InlineKeyboardButton(text=f'{p}%', callback_data=f'lz_down:{p}') for p in _DOWN_OPTIONS[:3]]
    row2 = [InlineKeyboardButton(text=f'{p}%', callback_data=f'lz_down:{p}') for p in _DOWN_OPTIONS[3:]]
    return InlineKeyboardMarkup(inline_keyboard=[
        row1, row2,
        [InlineKeyboardButton(
            text=_TEXT['back_list'].get(lang, _TEXT['back_list']['ru']),
            callback_data='lz_back:product',
        )],
    ])


def _build_term_kb(lang: str) -> InlineKeyboardMarkup:
    ml   = _MONTHS.get(lang, 'мес')
    row1 = [InlineKeyboardButton(text=f'{t} {ml}', callback_data=f'lz_term:{t}') for t in _TERM_OPTIONS[:3]]
    row2 = [InlineKeyboardButton(text=f'{t} {ml}', callback_data=f'lz_term:{t}') for t in _TERM_OPTIONS[3:]]
    return InlineKeyboardMarkup(inline_keyboard=[
        row1, row2,
        [InlineKeyboardButton(
            text=_TEXT['back'].get(lang, _TEXT['back']['ru']),
            callback_data='lz_back:down',
        )],
    ])


def _build_result_kb(lang: str, site_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_TEXT['apply'].get(lang, _TEXT['apply']['ru']),
            callback_data='lz_apply',
        )],
        [
            InlineKeyboardButton(
                text=_TEXT['change_params'].get(lang, _TEXT['change_params']['ru']),
                callback_data='lz_back:down',
            ),
            InlineKeyboardButton(
                text=_TEXT['details'].get(lang, _TEXT['details']['ru']),
                url=f'{site_url}/lizing/',
            ),
        ],
        [InlineKeyboardButton(
            text=_TEXT['new_calc'].get(lang, _TEXT['new_calc']['ru']),
            callback_data='lz_back:browse',
        )],
    ])


# ─── Форматирование ──────────────────────────────────────────────────────────

def _format_product_card(product: dict, index: int, total: int, lang: str) -> str:
    """Карточка продукта в лизинге — как в каталоге."""
    lines = [f"🚛 <b>{product['title']}</b>"]

    if product.get('year'):
        year_label = {'ru': 'Год', 'uz': 'Yil', 'en': 'Year'}.get(lang, 'Year')
        lines.append(f"{year_label}: {product['year']}")

    price_label = {'ru': 'Цена', 'uz': 'Narx', 'en': 'Price'}.get(lang, 'Цена')
    lines.append(f"💰 {price_label}: <b>{product['price_str']}</b>")

    if product.get('card_specs'):
        lines.append('')
        lines.extend(f"• {s}" for s in product['card_specs'])

    if product.get('features'):
        feat_label = {
            'ru': 'Комплектация',
            'uz': 'Komplektatsiya',
            'en': 'Equipment',
        }.get(lang, 'Equipment')
        lines.append('')
        lines.append(f"<b>{feat_label}:</b>")
        lines.extend(f"• {f}" for f in product['features'])

    of_label = {'ru': 'из', 'uz': 'dan', 'en': 'of'}.get(lang, 'из')
    lines.append(f"\n<i>{index + 1} {of_label} {total}</i>")

    return '\n'.join(lines) 


def _format_result(calc: dict, title: str, lang: str) -> str:
    ml  = _MONTHS.get(lang, 'мес')
    cur = _CURRENCY.get(lang, 'сум')
    templates = {
        'ru': (
            f"📊 <b>Расчёт лизинга</b>\n\n"
            f"🚛 <b>{title}</b>\n\n"
            f"💰 Цена: <b>{_fmt(calc['price'])} {cur}</b>\n"
            f"💵 Взнос ({calc['down_pct']}%): <b>{_fmt(calc['down_payment'])} {cur}</b>\n"
            f"🏦 Финансирование: <b>{_fmt(calc['financing'])} {cur}</b>\n"
            f"📅 Срок: <b>{calc['term']} {ml}</b>\n"
            f"📈 Ставка: <b>{calc['annual_rate'] * 100:.1f}% годовых</b>\n\n"
            f"✅ <b>Платёж: {_fmt(calc['monthly_payment'])} {cur}/мес</b>\n\n"
            f"<i>Предварительный расчёт. Уточняйте у менеджера.</i>"
        ),
        'uz': (
            f"📊 <b>Lizing hisobi</b>\n\n"
            f"🚛 <b>{title}</b>\n\n"
            f"💰 Narx: <b>{_fmt(calc['price'])} {cur}</b>\n"
            f"💵 To'lov ({calc['down_pct']}%): <b>{_fmt(calc['down_payment'])} {cur}</b>\n"
            f"🏦 Moliyalashtirish: <b>{_fmt(calc['financing'])} {cur}</b>\n"
            f"📅 Muddat: <b>{calc['term']} {ml}</b>\n"
            f"📈 Stavka: <b>{calc['annual_rate'] * 100:.1f}% yillik</b>\n\n"
            f"✅ <b>To'lov: {_fmt(calc['monthly_payment'])} {cur}/oy</b>\n\n"
            f"<i>Dastlabki hisob. Menejer bilan aniqlashtiring.</i>"
        ),
        'en': (
            f"📊 <b>Leasing Calculation</b>\n\n"
            f"🚛 <b>{title}</b>\n\n"
            f"💰 Price: <b>{_fmt(calc['price'])} {cur}</b>\n"
            f"💵 Down ({calc['down_pct']}%): <b>{_fmt(calc['down_payment'])} {cur}</b>\n"
            f"🏦 Financing: <b>{_fmt(calc['financing'])} {cur}</b>\n"
            f"📅 Term: <b>{calc['term']} {ml}</b>\n"
            f"📈 Rate: <b>{calc['annual_rate'] * 100:.1f}% p.a.</b>\n\n"
            f"✅ <b>Payment: {_fmt(calc['monthly_payment'])} {cur}/mo</b>\n\n"
            f"<i>Preliminary. Please confirm with manager.</i>"
        ),
    }
    return templates.get(lang, templates['ru'])
# ─── Отправка карточки продукта ──────────────────────────────────────────────

async def _show_product_card(
    callback: CallbackQuery,
    products: list[dict],
    index: int,
    lang: str,
    edit: bool = False,
) -> None:
    product = products[index]
    text    = _format_product_card(product, index, len(products), lang)
    kb      = _build_product_card_kb(index, len(products), lang)

    image_path = product.get('image_path')
    photo = None
    if image_path:
        try:
            photo = await read_file(image_path)  # async-безопасно
        except OSError as exc:
            logger.warning('Photo read failed product_id=%s: %s', product.get('id'), exc)

    if edit:
        if photo:
            try:
                await callback.message.edit_media(
                    media=InputMediaPhoto(
                        media=BufferedInputFile(photo, filename='product.jpg'),
                        caption=text,
                    ),
                    reply_markup=kb,
                )
                return
            except Exception as exc:
                logger.warning('edit_media failed: %s', exc)
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            pass
        return

    if photo:
        try:
            await callback.message.answer_photo(
                photo=BufferedInputFile(photo, filename='product.jpg'),
                caption=text,
                reply_markup=kb,
            )
            return
        except Exception as exc:
            logger.warning('answer_photo failed: %s', exc)

    await callback.message.answer(text, reply_markup=kb)


# ═══════════════════════════════════════════════════════════════════════════════
# ВХОД
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.in_(LEASING_TRIGGERS))
async def handle_leasing_enter(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()
    await state.set_state(LeasingStates.choose_browse_mode)
    await state.update_data(language=lang)
    await message.answer(
        _TEXT['enter'].get(lang, _TEXT['enter']['ru']),
        reply_markup=_build_browse_kb(lang),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ВЫБОР РЕЖИМА
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('lz_browse:'))
async def handle_lz_browse(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    mode = callback.data.split(':')[1]

    await state.update_data(browse_mode=mode)

    if mode == 'by_type':
        categories = await _get_categories_with_prices(lang)
        if not categories:
            await callback.answer(_TEXT['no_products'].get(lang), show_alert=True)
            return
        await state.set_state(LeasingStates.choose_category)
        await callback.message.edit_text(
            _TEXT['choose_category'].get(lang, _TEXT['choose_category']['ru']),
            reply_markup=_build_categories_kb(categories, lang),
        )
    else:
        subcategories = await _get_subcategories_with_prices(lang)
        if not subcategories:
            await callback.answer(_TEXT['no_products'].get(lang), show_alert=True)
            return
        await state.set_state(LeasingStates.choose_subcategory)
        await callback.message.edit_text(
            _TEXT['choose_platform'].get(lang, _TEXT['choose_platform']['ru']),
            reply_markup=_build_subcategories_kb(subcategories, lang),
        )
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# ВЫБОР КАТЕГОРИИ
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('lz_cat:'))
async def handle_lz_category(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data     = await state.get_data()
    lang     = data.get('language', 'ru')
    category = callback.data.split(':')[1]

    products = await _get_products_by_filter(lang, category=category)
    if not products:
        await callback.answer(_TEXT['no_products'].get(lang), show_alert=True)
        return

    await state.set_state(LeasingStates.choose_product)
    await state.update_data(products=products, product_index=0, selected_category=category)
    await _show_product_card(callback, products, 0, lang)
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# ВЫБОР ПЛАТФОРМЫ
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('lz_sub:'))
async def handle_lz_subcategory(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data        = await state.get_data()
    lang        = data.get('language', 'ru')
    subcategory = callback.data.split(':')[1]

    products = await _get_products_by_filter(lang, subcategory=subcategory)
    if not products:
        await callback.answer(_TEXT['no_products'].get(lang), show_alert=True)
        return

    await state.set_state(LeasingStates.choose_product)
    await state.update_data(products=products, product_index=0, selected_subcategory=subcategory)
    await _show_product_card(callback, products, 0, lang)
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# НАВИГАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('lz_nav:'))
async def handle_lz_nav(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data     = await state.get_data()
    lang     = data.get('language', 'ru')
    products = data.get('products', [])
    index    = int(callback.data.split(':')[1])

    if not products or index >= len(products):
        await callback.answer()
        return

    await state.update_data(product_index=index)
    await _show_product_card(callback, products, index, lang, edit=True)
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# ВЫБРАТЬ МОДЕЛЬ → ВЗНОС
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('lz_select:'))
async def handle_lz_select(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data     = await state.get_data()
    lang     = data.get('language', 'ru')
    products = data.get('products', [])
    index    = int(callback.data.split(':')[1])

    if not products or index >= len(products):
        await callback.answer()
        return

    product = products[index]
    await state.update_data(
        selected_product_title=product['title'],
        selected_product_price=product['price'],
        selected_product_slug=product.get('slug', ''),
    )
    await state.set_state(LeasingStates.choose_down_payment)

    text = (
        f"🚛 <b>{product['title']}</b>\n\n"
        f"{_TEXT['choose_down'].get(lang, _TEXT['choose_down']['ru'])}"
    )
    try:
        await callback.message.edit_text(text, reply_markup=_build_down_kb(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=_build_down_kb(lang))

    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# ВЗНОС → СРОК
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('lz_down:'))
async def handle_lz_down(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data     = await state.get_data()
    lang     = data.get('language', 'ru')
    down_pct = int(callback.data.split(':')[1])

    await state.update_data(selected_down_pct=down_pct)
    await state.set_state(LeasingStates.choose_term)

    down_label = {'ru': 'Взнос', 'uz': "To'lov", 'en': 'Down'}.get(lang, 'Взнос')
    await callback.message.edit_text(
        f"🚛 <b>{data['selected_product_title']}</b>\n"
        f"💵 {down_label}: <b>{down_pct}%</b>\n\n"
        f"{_TEXT['choose_term'].get(lang, _TEXT['choose_term']['ru'])}",
        reply_markup=_build_term_kb(lang),
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# СРОК → РЕЗУЛЬТАТ
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('lz_term:'))
async def handle_lz_term(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    price = data.get('selected_product_price')
    down_pct = data.get('selected_down_pct')
    if not price or down_pct is None:
        await callback.answer(
            {'ru': 'Сессия устарела. Начните расчёт заново.', 'uz': 'Sessiya eskirdi.', 'en': 'Session expired. Please restart.'}.get(lang, 'Session expired.'),
            show_alert=True,
        )
        await state.clear()
        return

    term = int(callback.data.split(':')[1])
    calc = _calculate(price, down_pct, term)

    await state.update_data(calc=calc)
    await state.set_state(LeasingStates.confirm)

    config   = await get_config()
    site_url = config.site_url if config else 'https://faw.uz'

    try:
        await callback.message.edit_text(
            _format_result(calc, data['selected_product_title'], lang),
            reply_markup=_build_result_kb(lang, site_url),
        )
    except Exception:
        await callback.message.answer(
            _format_result(calc, data.get('selected_product_title', ''), lang),
            reply_markup=_build_result_kb(lang, site_url),
        )
    await callback.answer()



# ═══════════════════════════════════════════════════════════════════════════════
# НАЗАД — универсальный
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('lz_back:'))
async def handle_lz_back(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data   = await state.get_data()
    lang   = data.get('language', 'ru')
    target = callback.data.split(':')[1]

    if target == 'browse':
        await state.set_state(LeasingStates.choose_browse_mode)
        try:
            await callback.message.edit_text(
                _TEXT['enter'].get(lang, _TEXT['enter']['ru']),
                reply_markup=_build_browse_kb(lang),
            )
        except Exception:
            await callback.message.answer(
                _TEXT['enter'].get(lang, _TEXT['enter']['ru']),
                reply_markup=_build_browse_kb(lang),
            )

    elif target == 'product':  
        products = data.get('products', [])
        index    = data.get('product_index', 0)
        await state.set_state(LeasingStates.choose_product)
        if products:
            await _show_product_card(callback, products, index, lang, edit=True)
        else:
            await state.set_state(LeasingStates.choose_browse_mode)
            try:
                await callback.message.edit_text(
                    _TEXT['enter'].get(lang, _TEXT['enter']['ru']),
                    reply_markup=_build_browse_kb(lang),
                )
            except Exception:
                await callback.message.answer(
                    _TEXT['enter'].get(lang, _TEXT['enter']['ru']),
                    reply_markup=_build_browse_kb(lang),
                )

    elif target == 'down':
        await state.set_state(LeasingStates.choose_down_payment)
        title = data.get('selected_product_title', '')
        text = (
            f"<b>{title}</b>\n\n"
            f"{_TEXT['choose_down'].get(lang, _TEXT['choose_down']['ru'])}"
        )
        try:
            await callback.message.edit_text(text, reply_markup=_build_down_kb(lang))
        except Exception:
            await callback.message.answer(text, reply_markup=_build_down_kb(lang))

    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# ОСТАВИТЬ ЗАЯВКУ
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == 'lz_apply')
async def handle_lz_apply(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    data = await state.get_data()
    lang = data.get('language', 'ru')
    calc = data.get('calc', {})

    if not user or not user.phone:
        await callback.answer(
            _TEXT['no_phone'].get(lang, _TEXT['no_phone']['ru']),
            show_alert=True,
        )
        return

    ml  = _MONTHS.get(lang, 'мес')
    cur = _CURRENCY.get(lang, 'сум')  

    message_text = (
        f"Лизинг\n"
        f"Модель: {data.get('selected_product_title', '—')}\n"
        f"Цена: {_fmt(calc.get('price', 0))} {cur}\n"
        f"Взнос: {calc.get('down_pct', 0)}% ({_fmt(calc.get('down_payment', 0))} {cur})\n"
        f"Срок: {calc.get('term', 0)} {ml}\n"
        f"Ставка: {calc.get('annual_rate', 0) * 100:.1f}%\n"
        f"Платёж: {_fmt(calc.get('monthly_payment', 0))} {cur}/{ml}"
    )

    lead = await _create_lead({
        'name':          user.first_name or '',
        'phone':         user.phone,
        'region':        user.region or '',
        'product_title': data.get('selected_product_title', ''),
        'message':       message_text,
    })

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    main_menu = await get_main_menu_keyboard(lang)

    if lead:
        await callback.message.answer(
            _TEXT['lead_success'].get(lang, _TEXT['lead_success']['ru']),
            reply_markup=main_menu,
        )
        logger.info(
            'Leasing lead: telegram_id=%s lead_id=%s',
            callback.from_user.id, lead.id,
        )
    else:
        await callback.message.answer(
            _TEXT['lead_error'].get(lang, _TEXT['lead_error']['ru']),
            reply_markup=main_menu,
        )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == 'lz_noop')
async def handle_lz_noop(callback: CallbackQuery):
    await callback.answer()