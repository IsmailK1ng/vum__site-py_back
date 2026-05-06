import logging
import re

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from asgiref.sync import sync_to_async

from main.models import TelegramUser, REGION_LABELS
from main.services.telegram.bot_service import BotService
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.states.fsm import EditProfileStates
from main.services.telegram.triggers import PROFILE_TRIGGERS
from main.services.telegram.utils import get_message, read_file

logger = logging.getLogger('bot')
router = Router(name='profile')

LANGUAGE_DISPLAY = {'ru': 'Русский', 'uz': "O'zbekcha", 'en': 'English'}

_DIVIDER = '─' * 22

_PROFILE_HEADER = {
    'ru': '<b>Профиль</b>',
    'uz': '<b>Profil</b>',
    'en': '<b>Profile</b>',
}

_PROFILE_FIELDS = {
    'ru': 'Имя: <b>{first_name}</b>\nТелефон: <b>{phone}</b>\nРегион: <b>{region}</b>\nЯзык: <b>{lang_display}</b>',
    'uz': 'Ism: <b>{first_name}</b>\nTelefon: <b>{phone}</b>\nViloyat: <b>{region}</b>\nTil: <b>{lang_display}</b>',
    'en': 'Name: <b>{first_name}</b>\nPhone: <b>{phone}</b>\nRegion: <b>{region}</b>\nLanguage: <b>{lang_display}</b>',
}

_TD_HEADER = {
    'ru': '<b>Активный тест-драйв</b>',
    'uz': '<b>Faol test-drayv</b>',
    'en': '<b>Active test drive</b>',
}

_TD_FIELDS = {
    'ru': '{product}\n{date}\nСтатус: {status}',
    'uz': '{product}\n{date}\nHolat: {status}',
    'en': '{product}\n{date}\nStatus: {status}',
}

_TD_STATUS_LABELS = {
    'new':       {'ru': 'Новая',        'uz': 'Yangi',        'en': 'New'},
    'confirmed': {'ru': 'Подтверждена', 'uz': 'Tasdiqlangan', 'en': 'Confirmed'},
}

_WISHLIST_BTN = {
    'ru': 'Избранное ({count})',
    'uz': 'Sevimlilar ({count})',
    'en': 'Favourites ({count})',
}

_WISHLIST_EMPTY_BTN = {
    'ru': 'Избранное пусто',
    'uz': "Sevimlilar bo'sh",
    'en': 'No favourites yet',
}

_WISHLIST_HEADER = {
    'ru': '<b>Избранные модели:</b>',
    'uz': '<b>Sevimli modellar:</b>',
    'en': '<b>Favourite models:</b>',
}

_WISHLIST_EMPTY_ALERT = {
    'ru': 'Избранное пусто. Добавляйте модели из каталога.',
    'uz': "Sevimlilar bo'sh. Katalogdan modellar qo'shing.",
    'en': 'No favourites yet. Add models from the catalogue.',
}

_CANCEL_TD_BTN = {
    'ru': 'Отменить тест-драйв',
    'uz': 'Test-drayvni bekor qilish',
    'en': 'Cancel test drive',
}

_EDIT_BTN = {
    'ru': '✏️ Редактировать профиль',
    'uz': '✏️ Profilni tahrirlash',
    'en': '✏️ Edit profile',
}

_CANCEL_SUCCESS = {
    'ru': 'Тест-драйв отменён. Можете записаться снова.',
    'uz': 'Test-drayv bekor qilindi. Qayta yozilishingiz mumkin.',
    'en': 'Test drive cancelled. You can book again.',
}

_CANCEL_FAIL = {
    'ru': 'Не удалось отменить. Возможно, заявка уже отменена.',
    'uz': "Bekor qilib bo'lmadi. Ehtimol, allaqachon bekor qilingan.",
    'en': 'Could not cancel. It may already be cancelled.',
}

_NOT_REGISTERED = {
    'ru': 'Необходимо зарегистрироваться.',
    'uz': "Ro'yxatdan o'tish kerak.",
    'en': 'Registration required.',
}

_MODEL_NOT_FOUND = {
    'ru': 'Модель не найдена.',
    'uz': 'Model topilmadi.',
    'en': 'Model not found.',
}

_CARD_LABELS = {
    'site':   {'ru': 'Подробнее на сайте',    'uz': 'Saytda batafsil',             'en': 'Full specs on website'},
    'price':  {'ru': 'Узнать цену',            'uz': 'Narxni bilish',               'en': 'Get price'},
    'td':     {'ru': 'Тест-драйв',             'uz': 'Test-drayv',                  'en': 'Test drive'},
    'remove': {'ru': 'Убрать из избранного',   'uz': 'Sevimlilardan olib tashlash', 'en': 'Remove from favourites'},
}

# ─── Редактирование профиля — тексты ─────────────────────────────────────────

_EDIT_ASK_NAME = {
    'ru': 'Введите новое имя или нажмите «Оставить текущее»:\n\nТекущее: <b>{current}</b>',
    'uz': "Yangi ismni kiriting yoki «Hozirgicha qoldirish»ni bosing:\n\nHozirgi: <b>{current}</b>",
    'en': 'Enter a new name or tap "Keep current":\n\nCurrent: <b>{current}</b>',
}

_EDIT_ASK_PHONE = {
    'ru': 'Введите новый номер телефона или нажмите «Оставить текущее»:\n\nТекущий: <b>{current}</b>',
    'uz': "Yangi telefon raqamini kiriting yoki «Hozirgicha qoldirish»ni bosing:\n\nHozirgi: <b>{current}</b>",
    'en': 'Enter a new phone number or tap "Keep current":\n\nCurrent: <b>{current}</b>',
}

_KEEP_BTN = {
    'ru': 'Оставить текущее',
    'uz': 'Hozirgicha qoldirish',
    'en': 'Keep current',
}

_CANCEL_EDIT_BTN = {
    'ru': 'Отменить',
    'uz': 'Bekor qilish',
    'en': 'Cancel',
}

_EDIT_SUCCESS = {
    'ru': '✅ Профиль обновлён.',
    'uz': '✅ Profil yangilandi.',
    'en': '✅ Profile updated.',
}

_EDIT_CANCELLED = {
    'ru': 'Редактирование отменено.',
    'uz': 'Tahrirlash bekor qilindi.',
    'en': 'Editing cancelled.',
}

_INVALID_PHONE = {
    'ru': 'Некорректный номер. Введите номер в формате +998901234567 или 998901234567:',
    'uz': "Noto'g'ri raqam. +998901234567 yoki 998901234567 formatida kiriting:",
    'en': 'Invalid number. Enter in format +998901234567 or 998901234567:',
}

_INVALID_NAME = {
    'ru': 'Имя слишком короткое. Введите минимум 2 символа:',
    'uz': "Ism juda qisqa. Kamida 2 ta belgi kiriting:",
    'en': 'Name is too short. Enter at least 2 characters:',
}

# Паттерн: опциональный +, затем цифры, итого 9–15 цифр
_PHONE_RE = re.compile(r'^\+?\d{9,15}$')


# ─── Async обёртки ───────────────────────────────────────────────────────────

@sync_to_async
def _get_active_td(user: TelegramUser):
    return BotService.get_active_test_drive(user)


@sync_to_async
def _get_wishlist(user: TelegramUser, lang: str) -> list[dict]:
    return BotService.get_wishlist(user, lang)


@sync_to_async
def _cancel_td(td_id: int, user: TelegramUser) -> bool:
    return BotService.cancel_test_drive(td_id, user)


@sync_to_async
def _get_product_detail(product_id: int, lang: str):
    return BotService.get_product_detail(product_id, lang)


@sync_to_async
def _toggle_wishlist(user: TelegramUser, product_id: int) -> bool:
    return BotService.toggle_wishlist(user, product_id)


@sync_to_async
def _get_config():
    return BotService.get_config()


@sync_to_async
def _update_user(telegram_id: int, **kwargs):
    return BotService.update_user(telegram_id, **kwargs)


# ─── Построение профиля ──────────────────────────────────────────────────────

def _build_profile_text(
    user: TelegramUser,
    lang: str,
    active_td=None,
) -> str:
    region_key = user.region or ''
    region_display = REGION_LABELS.get(region_key, {}).get(lang) or region_key or '—'

    lines = [
        _PROFILE_HEADER.get(lang, _PROFILE_HEADER['ru']),
        _DIVIDER,
        _PROFILE_FIELDS.get(lang, _PROFILE_FIELDS['ru']).format(
            first_name=user.first_name or '—',
            phone=user.phone or '—',
            region=region_display,
            lang_display=LANGUAGE_DISPLAY.get(user.language, user.language),
        ),
    ]

    if active_td:
        product_title = '—'
        if active_td.product:
            product_title = (
                getattr(active_td.product, f'title_{lang}', None)
                or active_td.product.title
                or '—'
            )

        status_label = _TD_STATUS_LABELS.get(
            active_td.status, {}
        ).get(lang, active_td.status)

        lines += [
            _DIVIDER,
            _TD_HEADER.get(lang, _TD_HEADER['ru']),
            _TD_FIELDS.get(lang, _TD_FIELDS['ru']).format(
                product=product_title,
                date=active_td.preferred_date.strftime('%d.%m.%Y') if active_td.preferred_date else '—',
                status=status_label,
            ),
        ]

    return '\n'.join(lines)


def _build_profile_keyboard(
    lang: str,
    wishlist_count: int,
    active_td=None,
) -> InlineKeyboardMarkup:
    rows = []

    if wishlist_count > 0:
        rows.append([InlineKeyboardButton(
            text=_WISHLIST_BTN.get(lang, _WISHLIST_BTN['ru']).format(count=wishlist_count),
            callback_data='profile_wishlist',
        )])
    else:
        rows.append([InlineKeyboardButton(
            text=_WISHLIST_EMPTY_BTN.get(lang, _WISHLIST_EMPTY_BTN['ru']),
            callback_data='profile_wishlist_empty',
        )])

    # Кнопка редактирования профиля
    rows.append([InlineKeyboardButton(
        text=_EDIT_BTN.get(lang, _EDIT_BTN['ru']),
        callback_data='profile_edit',
    )])

    if active_td:
        rows.append([InlineKeyboardButton(
            text=_CANCEL_TD_BTN.get(lang, _CANCEL_TD_BTN['ru']),
            callback_data=f'cancel_td:{active_td.id}',
        )])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_keep_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками «Оставить текущее» и «Отменить»."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_KEEP_BTN[lang])],
            [KeyboardButton(text=_CANCEL_EDIT_BTN[lang])],
        ],
        resize_keyboard=True,
    )


def _build_wishlist_keyboard(items: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=item['title'],
            callback_data=f"wl_open:{item['id']}",
        )]
        for item in items
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_product_keyboard(
    product: dict,
    lang: str,
    site_url: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_CARD_LABELS['site'].get(lang, _CARD_LABELS['site']['ru']),
            url=f"{site_url}/products/{product['slug']}/",
        )],
        [InlineKeyboardButton(
            text=_CARD_LABELS['price'].get(lang, _CARD_LABELS['price']['ru']),
            callback_data=f"lead_from_catalog:{product['id']}",
        )],
        [InlineKeyboardButton(
            text=_CARD_LABELS['td'].get(lang, _CARD_LABELS['td']['ru']),
            callback_data=f"td_from_catalog:{product['id']}",
        )],
        [InlineKeyboardButton(
            text=_CARD_LABELS['remove'].get(lang, _CARD_LABELS['remove']['ru']),
            callback_data=f"wl_remove:{product['id']}",
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
            if product.get('price_is_from') else ''
        )
        lines.append(f"{price_label}: {prefix}{product['price']}")

    if product.get('card_specs'):
        lines.append('')
        lines.extend(f"• {s}" for s in product['card_specs'])

    return '\n'.join(lines)


def _parse_callback_int(data: str) -> int | None:
    try:
        return int(data.split(':')[1])
    except (IndexError, ValueError):
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC
# ═══════════════════════════════════════════════════════════════════════════════

async def show_profile(message: Message, user: TelegramUser, lang: str) -> None:
    active_td = await _get_active_td(user)
    wishlist = await _get_wishlist(user, lang)
    text = _build_profile_text(user, lang, active_td)
    keyboard = _build_profile_keyboard(lang, len(wishlist), active_td)
    await message.answer(text, reply_markup=keyboard)
    logger.info('Profile viewed: telegram_id=%s', message.from_user.id)


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS — профиль
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(StateFilter('*'), F.text.in_(PROFILE_TRIGGERS))
async def handle_profile(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()

    if not user:
        text = await get_message('main_menu_text', lang)
        await message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
        return

    await show_profile(message, user, lang)


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS — редактирование профиля
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == 'profile_edit')
async def handle_profile_edit_start(
    callback: CallbackQuery,
    state: FSMContext,
    user: TelegramUser | None,
):
    if not user:
        await callback.answer(_NOT_REGISTERED['ru'], show_alert=True)
        return

    lang = user.language or 'ru'
    await state.set_state(EditProfileStates.edit_name)
    await state.update_data(
        edit_lang=lang,
        edit_telegram_id=user.telegram_id,
        # Сохраняем текущие значения — понадобятся если пользователь нажмёт «Оставить»
        current_name=user.first_name or '',
        current_phone=user.phone or '',
    )

    await callback.message.answer(
        _EDIT_ASK_NAME[lang].format(current=user.first_name or '—'),
        reply_markup=_build_keep_keyboard(lang),
    )
    await callback.answer()


@router.message(EditProfileStates.edit_name)
async def handle_edit_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('edit_lang', 'ru')
    keep_btn = _KEEP_BTN[lang]
    cancel_btn = _CANCEL_EDIT_BTN[lang]

    if message.text == cancel_btn:
        await state.clear()
        await message.answer(
            _EDIT_CANCELLED[lang],
            reply_markup=await get_main_menu_keyboard(lang),
        )
        return

    if message.text == keep_btn:
        # Имя не меняем — переходим к телефону с текущим именем
        new_name = data.get('current_name', '')
    else:
        text = (message.text or '').strip()
        if len(text) < 2:
            await message.answer(
                _INVALID_NAME[lang],
                reply_markup=_build_keep_keyboard(lang),
            )
            return
        new_name = text

    await state.update_data(new_name=new_name)
    await state.set_state(EditProfileStates.edit_phone)

    current_phone = data.get('current_phone', '') or '—'
    await message.answer(
        _EDIT_ASK_PHONE[lang].format(current=current_phone),
        reply_markup=_build_keep_keyboard(lang),
    )


@router.message(EditProfileStates.edit_phone)
async def handle_edit_phone(message: Message, state: FSMContext, user: TelegramUser | None):
    data = await state.get_data()
    lang = data.get('edit_lang', 'ru')
    keep_btn = _KEEP_BTN[lang]
    cancel_btn = _CANCEL_EDIT_BTN[lang]

    if message.text == cancel_btn:
        await state.clear()
        await message.answer(
            _EDIT_CANCELLED[lang],
            reply_markup=await get_main_menu_keyboard(lang),
        )
        return

    if message.text == keep_btn:
        new_phone = data.get('current_phone', '')
    else:
        phone = (message.text or '').strip().replace(' ', '').replace('-', '')
        if not _PHONE_RE.match(phone):
            await message.answer(
                _INVALID_PHONE[lang],
                reply_markup=_build_keep_keyboard(lang),
            )
            return
        new_phone = phone

    # Сохраняем в БД через BotService.update_user
    telegram_id = data.get('edit_telegram_id')
    new_name = data.get('new_name', '')

    updated_user = await _update_user(
        telegram_id,
        first_name=new_name,
        phone=new_phone,
    )

    await state.clear()

    if updated_user:
        logger.info(
            'Profile updated: telegram_id=%s name=%s phone=%s',
            telegram_id, new_name, new_phone,
        )
        await message.answer(
            _EDIT_SUCCESS[lang],
            reply_markup=ReplyKeyboardRemove(),
        )
        # Показываем обновлённый профиль сразу
        await show_profile(message, updated_user, lang)
    else:
        logger.error('Profile update failed: telegram_id=%s', telegram_id)
        await message.answer(
            {'ru': 'Ошибка сохранения. Попробуйте позже.',
             'uz': 'Saqlashda xatolik. Keyinroq urinib ko\'ring.',
             'en': 'Save error. Please try again later.'}.get(lang, 'Error.'),
            reply_markup=await get_main_menu_keyboard(lang),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS — избранное
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == 'profile_wishlist')
async def handle_wishlist(callback: CallbackQuery, user: TelegramUser | None):
    if not user:
        await callback.answer(_NOT_REGISTERED['ru'], show_alert=True)
        return

    lang = user.language or 'ru'
    wishlist = await _get_wishlist(user, lang)

    if not wishlist:
        await callback.answer(
            _WISHLIST_EMPTY_ALERT.get(lang, _WISHLIST_EMPTY_ALERT['ru']),
            show_alert=True,
        )
        return

    header = _WISHLIST_HEADER.get(lang, _WISHLIST_HEADER['ru'])
    keyboard = _build_wishlist_keyboard(wishlist, lang)
    await callback.message.answer(header, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == 'profile_wishlist_empty')
async def handle_wishlist_empty(callback: CallbackQuery, user: TelegramUser | None):
    lang = user.language if user else 'ru'
    await callback.answer(
        _WISHLIST_EMPTY_ALERT.get(lang, _WISHLIST_EMPTY_ALERT['ru']),
        show_alert=True,
    )


@router.callback_query(F.data.startswith('wl_open:'))
async def handle_wishlist_open(callback: CallbackQuery, user: TelegramUser | None):
    if not user:
        await callback.answer(_NOT_REGISTERED['ru'], show_alert=True)
        return

    lang = user.language or 'ru'
    product_id = _parse_callback_int(callback.data)
    if product_id is None:
        await callback.answer()
        return

    product = await _get_product_detail(product_id, lang)
    if not product:
        await callback.answer(
            _MODEL_NOT_FOUND.get(lang, _MODEL_NOT_FOUND['ru']),
            show_alert=True,
        )
        return

    config = await _get_config()
    site_url = config.site_url if config else 'https://faw.uz'
    caption = _format_product_card(product, lang)
    keyboard = _build_product_keyboard(product, lang, site_url)

    image_path = product.get('image_path')
    if image_path:
        try:
            photo_bytes = await read_file(image_path)
            await callback.message.answer_photo(
                photo=BufferedInputFile(photo_bytes, filename='product.jpg'),
                caption=caption,
                reply_markup=keyboard,
            )
            await callback.answer()
            return
        except OSError as exc:
            logger.warning('wl_open photo failed product_id=%s: %s', product_id, exc)

    await callback.message.answer(caption, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('wl_remove:'))
async def handle_wishlist_remove(callback: CallbackQuery, user: TelegramUser | None):
    if not user:
        await callback.answer(_NOT_REGISTERED['ru'], show_alert=True)
        return

    lang = user.language or 'ru'
    product_id = _parse_callback_int(callback.data)
    if product_id is None:
        await callback.answer()
        return

    await _toggle_wishlist(user, product_id)

    removed_text = {
        'ru': 'Убрано из избранного',
        'uz': 'Sevimlilardan olib tashlandi',
        'en': 'Removed from favourites',
    }
    await callback.answer(removed_text.get(lang, removed_text['ru']))

    try:
        await callback.message.delete()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS — отмена тест-драйва
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith('cancel_td:'))
async def handle_cancel_td(callback: CallbackQuery, user: TelegramUser | None):
    if not user:
        await callback.answer(_NOT_REGISTERED['ru'], show_alert=True)
        return

    lang = user.language or 'ru'
    td_id = _parse_callback_int(callback.data)
    if td_id is None:
        await callback.answer()
        return

    cancelled = await _cancel_td(td_id, user)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    text = (
        _CANCEL_SUCCESS.get(lang, _CANCEL_SUCCESS['ru'])
        if cancelled
        else _CANCEL_FAIL.get(lang, _CANCEL_FAIL['ru'])
    )
    await callback.message.answer(text, reply_markup=await get_main_menu_keyboard(lang))
    await callback.answer()