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
from main.services.telegram.bot_service import BotService
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.triggers import NEWS_TRIGGERS, PROMOTIONS_TRIGGERS
from main.services.telegram.utils import get_message, get_config, read_file

logger = logging.getLogger('bot')
router = Router(name='news')

_NEWS_LIMIT  = 20
_PROMO_LIMIT = 20

_NEWS_EMPTY = {
    'ru': 'Новостей пока нет.',
    'uz': "Hozircha yangiliklar yo'q.",
    'en': 'No news yet.',
}

_PROMO_EMPTY = {
    'ru': 'Активных акций нет.',
    'uz': "Faol aksiyalar yo'q.",
    'en': 'No active promotions.',
}

_READ_BTN = {
    'ru': 'Читать полностью',
    'uz': "To'liq o'qish",
    'en': 'Read more',
}

_MORE_BTN = {
    'ru': 'Подробнее',
    'uz': 'Batafsil',
    'en': 'More info',
}

_DAYS_LEFT = {
    'ru': 'До конца: {days} дн.',
    'uz': 'Tugashiga: {days} kun.',
    'en': 'Ends in: {days} days.',
}


# ─── Async обёртки ───────────────────────────────────────────────────────────

@sync_to_async
def _get_news(language: str, limit: int = _NEWS_LIMIT) -> list[dict]:
    return BotService.get_news(language, limit=limit)


@sync_to_async
def _get_promotions(language: str) -> list[dict]:
    return BotService.get_active_promotions(language)


# ─── Клавиатура ──────────────────────────────────────────────────────────────

def _build_nav_keyboard(
    index: int,
    total: int,
    url: str,
    btn_text: str,
    lang: str,
    cb_prefix: str,
) -> InlineKeyboardMarkup:
    nav_row = []

    if index > 0:
        nav_row.append(InlineKeyboardButton(
            text='◀️',
            callback_data=f'{cb_prefix}:{index - 1}:{lang}',
        ))

    nav_row.append(InlineKeyboardButton(
        text=f'{index + 1} / {total}',
        callback_data='news_noop',
    ))

    if index < total - 1:
        nav_row.append(InlineKeyboardButton(
            text='▶️',
            callback_data=f'{cb_prefix}:{index + 1}:{lang}',
        ))

    rows = [nav_row]
    if url:
        rows.append([InlineKeyboardButton(text=btn_text, url=url)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


# ─── Форматирование ──────────────────────────────────────────────────────────

def _format_news_text(item: dict) -> str:
    date_str = item['date'].strftime('%d.%m.%Y') if item.get('date') else ''
    lines = [f"<b>{item['title']}</b>"]
    if date_str:
        lines.append(date_str)
    if item.get('desc'):
        desc = item['desc'][:597] + '...' if len(item['desc']) > 600 else item['desc']
        lines.append(f"\n{desc}")
    return '\n'.join(lines)


def _format_promo_text(item: dict, lang: str) -> str:
    lines = [f"<b>{item['title']}</b>"]
    if item.get('description'):
        desc = item['description']
        if len(desc) > 600:
            desc = desc[:597] + '...'
        lines.append(desc)
    if item.get('end_date'):
        try:
            from django.utils import timezone
            days_left = (item['end_date'].date() - timezone.localdate()).days
            if 0 <= days_left <= 30:
                lines.append(_DAYS_LEFT.get(lang, _DAYS_LEFT['ru']).format(days=days_left))
        except Exception:
            pass
    return '\n\n'.join(lines)


# ─── Отправка карточки ───────────────────────────────────────────────────────

async def _send_item(
    message: Message,
    text: str,
    kb: InlineKeyboardMarkup,
    image_path: str | None,
    item_id: int,
    edit: bool = False,
) -> None:
    photo_bytes = None
    if image_path:
        try:
            photo_bytes = await read_file(image_path)  
        except OSError as exc:
            logger.warning('Photo read failed id=%s: %s', item_id, exc)

    if edit and photo_bytes:
        try:
            await message.edit_media(
                media=InputMediaPhoto(
                    media=BufferedInputFile(photo_bytes, filename='item.jpg'),
                    caption=text,
                ),
                reply_markup=kb,
            )
            return
        except Exception as exc:
            logger.warning('edit_media failed id=%s: %s', item_id, exc)

    if edit:
        try:
            await message.edit_caption(caption=text, reply_markup=kb)
            return
        except Exception:
            pass
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception as exc:
            logger.warning('edit failed id=%s: %s', item_id, exc)
        return

    if photo_bytes:
        try:
            await message.answer_photo(
                photo=BufferedInputFile(photo_bytes, filename='item.jpg'),
                caption=text,
                reply_markup=kb,
            )
            return
        except Exception as exc:
            logger.warning('answer_photo failed id=%s: %s', item_id, exc)

    await message.answer(text, reply_markup=kb)


# ═══════════════════════════════════════════════════════════════════════════════
# НОВОСТИ
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.in_(NEWS_TRIGGERS))
async def handle_news(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    await state.clear()
    lang = user.language if user else 'ru'
    main_menu = await get_main_menu_keyboard(lang)

    items = await _get_news(lang)
    if not items:
        await message.answer(_NEWS_EMPTY.get(lang, _NEWS_EMPTY['ru']), reply_markup=main_menu)
        return

    config = await get_config()
    site_url = config.site_url if config else 'https://faw.uz'

    # Отправляем главное меню как reply клавиатуру отдельно
    await message.answer(
        await get_message('news_title', lang),
        reply_markup=main_menu,
    )

    item = items[0]
    text = _format_news_text(item)
    url  = f"{site_url}/news/{item['slug']}/"
    kb   = _build_nav_keyboard(0, len(items), url, _READ_BTN.get(lang, _READ_BTN['ru']), lang, 'news_page')
    await _send_item(message, text, kb, item.get('image_path'), item['id'])


@router.callback_query(F.data.startswith('news_page:'))
async def handle_news_page(
    callback: CallbackQuery,
    user: TelegramUser | None,
):
    parts = callback.data.split(':')
    try:
        index = int(parts[1])
    except (IndexError, ValueError):
        await callback.answer()
        return

    lang = parts[2] if len(parts) > 2 else (user.language if user else 'ru')

    items = await _get_news(lang)
    if not items or index >= len(items):
        await callback.answer()
        return

    config = await get_config()
    site_url = config.site_url if config else 'https://faw.uz'

    item = items[index]
    text = _format_news_text(item)
    url  = f"{site_url}/news/{item['slug']}/"
    kb   = _build_nav_keyboard(index, len(items), url, _READ_BTN.get(lang, _READ_BTN['ru']), lang, 'news_page')
    await _send_item(callback.message, text, kb, item.get('image_path'), item['id'], edit=True)
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# АКЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.in_(PROMOTIONS_TRIGGERS))
async def handle_promotions(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    await state.clear()
    lang = user.language if user else 'ru'
    main_menu = await get_main_menu_keyboard(lang)

    items = await _get_promotions(lang)
    if not items:
        await message.answer(_PROMO_EMPTY.get(lang, _PROMO_EMPTY['ru']), reply_markup=main_menu)
        return

    config = await get_config()
    site_url = config.site_url if config else 'https://faw.uz'

    await message.answer(
        await get_message('promotions_title', lang),
        reply_markup=main_menu,
    )

    item     = items[0]
    text     = _format_promo_text(item, lang)
    btn_text = item.get('button_text') or _MORE_BTN.get(lang, _MORE_BTN['ru'])
    btn_url  = item.get('link') or site_url
    kb       = _build_nav_keyboard(0, len(items), btn_url, btn_text, lang, 'promo_page')
    await _send_item(message, text, kb, item.get('image_path'), item['id'])


@router.callback_query(F.data.startswith('promo_page:'))
async def handle_promo_page(
    callback: CallbackQuery,
    user: TelegramUser | None,
):
    parts = callback.data.split(':')
    try:
        index = int(parts[1])
    except (IndexError, ValueError):
        await callback.answer()
        return

    lang = parts[2] if len(parts) > 2 else (user.language if user else 'ru')

    items = await _get_promotions(lang)
    if not items or index >= len(items):
        await callback.answer()
        return

    config = await get_config()
    site_url = config.site_url if config else 'https://faw.uz'

    item     = items[index]
    text     = _format_promo_text(item, lang)
    btn_text = item.get('button_text') or _MORE_BTN.get(lang, _MORE_BTN['ru'])
    btn_url  = item.get('link') or site_url
    kb       = _build_nav_keyboard(index, len(items), btn_url, btn_text, lang, 'promo_page')
    await _send_item(callback.message, text, kb, item.get('image_path'), item['id'], edit=True)
    await callback.answer()


@router.callback_query(F.data == 'news_noop')
async def handle_news_noop(callback: CallbackQuery):
    await callback.answer()