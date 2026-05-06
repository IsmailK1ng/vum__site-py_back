import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Document,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from asgiref.sync import sync_to_async

from main.models import TelegramUser
from main.services.telegram.keyboards.main_menu import get_main_menu_keyboard
from main.services.telegram.states.fsm import PartnerStates
from main.services.telegram.triggers import PARTNER_TRIGGERS

logger = logging.getLogger('bot')
router = Router(name='partner')


_OFFER_TYPES = {
    'ru': [
        ('advertising', 'Реклама'),
        ('supplies',    'Поставки'),
        ('it',          'IT услуги'),
        ('finance',     'Финансы'),
        ('logistics',   'Логистика'),
        ('media',       'Медиа'),
        ('other',       'Другое'),
    ],
    'uz': [
        ('advertising', 'Reklama'),
        ('supplies',    "Ta'minot"),
        ('it',          'IT xizmatlar'),
        ('finance',     'Moliya'),
        ('logistics',   'Logistika'),
        ('media',       'Media'),
        ('other',       'Boshqa'),
    ],
    'en': [
        ('advertising', 'Advertising'),
        ('supplies',    'Supplies'),
        ('it',          'IT services'),
        ('finance',     'Finance'),
        ('logistics',   'Logistics'),
        ('media',       'Media'),
        ('other',       'Other'),
    ],
}


_TEXT = {
    'enter': {
        'ru': (
            '<b>Сотрудничество с FAW Uzbekistan</b>\n\n'
            'Если вы хотите предложить сотрудничество — заполните короткую форму.\n'
            'Ваше предложение поступит напрямую в отдел развития.\n\n'
            'Выберите тип предложения:'
        ),
        'uz': (
            "<b>FAW Uzbekistan bilan hamkorlik</b>\n\n"
            "Hamkorlik taklif qilmoqchi bo'lsangiz — qisqa formani to'ldiring.\n"
            "Taklifingiz to'g'ridan-to'g'ri rivojlanish bo'limiga tushadi.\n\n"
            'Taklif turini tanlang:'
        ),
        'en': (
            '<b>Partnership with FAW Uzbekistan</b>\n\n'
            'If you would like to propose cooperation — fill out a short form.\n'
            'Your proposal will go directly to the development department.\n\n'
            'Choose the type of proposal:'
        ),
    },
    'ask_name': {
        'ru': 'Введите ваше ФИО:',
        'uz': 'Ism-sharifingizni kiriting:',
        'en': 'Enter your full name:',
    },
    'ask_company': {
        'ru': 'Введите название вашей компании или фирмы:',
        'uz': 'Kompaniya yoki firma nomini kiriting:',
        'en': 'Enter your company or firm name:',
    },
    'ask_contact': {
        'ru': 'Введите ваш контакт — телефон или Telegram (@username):',
        'uz': "Kontaktingizni kiriting — telefon yoki Telegram (@username):",
        'en': 'Enter your contact — phone or Telegram (@username):',
    },
    'ask_file': {
        'ru': (
            'Прикрепите файл коммерческого предложения (PDF, Word, Excel)\n'
            'или нажмите <b>Пропустить</b> если файла нет.'
        ),
        'uz': (
            "Tijorat taklifingiz faylini yuklang (PDF, Word, Excel)\n"
            "yoki fayl bo'lmasa <b>O'tkazib yuborish</b> tugmasini bosing."
        ),
        'en': (
            'Attach your commercial proposal file (PDF, Word, Excel)\n'
            'or tap <b>Skip</b> if you have no file.'
        ),
    },
    'confirm': {
        'ru': (
            '<b>Проверьте данные:</b>\n\n'
            'Тип: <b>{offer_type}</b>\n'
            'ФИО: <b>{full_name}</b>\n'
            'Компания: <b>{company}</b>\n'
            'Контакт: <b>{contact}</b>\n'
            'Файл КП: <b>{file}</b>\n\n'
            'Всё верно?'
        ),
        'uz': (
            "<b>Ma'lumotlarni tekshiring:</b>\n\n"
            "Tur: <b>{offer_type}</b>\n"
            "Ism-sharif: <b>{full_name}</b>\n"
            "Kompaniya: <b>{company}</b>\n"
            "Kontakt: <b>{contact}</b>\n"
            "KT fayli: <b>{file}</b>\n\n"
            "Hammasi to'g'rimi?"
        ),
        'en': (
            '<b>Check your details:</b>\n\n'
            'Type: <b>{offer_type}</b>\n'
            'Full name: <b>{full_name}</b>\n'
            'Company: <b>{company}</b>\n'
            'Contact: <b>{contact}</b>\n'
            'Proposal file: <b>{file}</b>\n\n'
            'Is everything correct?'
        ),
    },
    'success': {
        'ru': (
            'Ваше предложение принято. '
            'Мы рассмотрим его и свяжемся с вами при необходимости.'
        ),
        'uz': (
            "Taklifingiz qabul qilindi. "
            "Biz uni ko'rib chiqamiz va kerak bo'lsa siz bilan bog'lanamiz."
        ),
        'en': (
            'Your proposal has been received. '
            'We will review it and contact you if needed.'
        ),
    },
    'error': {
        'ru': 'Ошибка при сохранении. Попробуйте позже.',
        'uz': "Saqlashda xatolik. Keyinroq urinib ko'ring.",
        'en': 'Save error. Please try again later.',
    },
    'cancelled': {
        'ru': 'Отменено.',
        'uz': 'Bekor qilindi.',
        'en': 'Cancelled.',
    },
    'invalid_name': {
        'ru': 'Слишком короткое имя. Введите минимум 2 символа:',
        'uz': 'Ism juda qisqa. Kamida 2 ta belgi kiriting:',
        'en': 'Name is too short. Enter at least 2 characters:',
    },
    'invalid_company': {
        'ru': 'Слишком короткое название. Введите минимум 2 символа:',
        'uz': 'Nom juda qisqa. Kamida 2 ta belgi kiriting:',
        'en': 'Too short. Enter at least 2 characters:',
    },
    'invalid_contact': {
        'ru': 'Введите корректный телефон или Telegram (@username):',
        'uz': "To'g'ri telefon yoki Telegram (@username) kiriting:",
        'en': 'Enter a valid phone or Telegram (@username):',
    },
    'invalid_file': {
        'ru': 'Принимаются только файлы PDF, Word или Excel. Попробуйте ещё раз или нажмите Пропустить:',
        'uz': "Faqat PDF, Word yoki Excel fayllar qabul qilinadi. Qayta urinib ko'ring yoki O'tkazib yuborishni bosing:",
        'en': 'Only PDF, Word or Excel files are accepted. Try again or tap Skip:',
    },
    'skip': {
        'ru': 'Пропустить',
        'uz': "O'tkazib yuborish",
        'en': 'Skip',
    },
    'cancel': {
        'ru': 'Отменить',
        'uz': 'Bekor qilish',
        'en': 'Cancel',
    },
    'yes': {
        'ru': 'Да, отправить',
        'uz': 'Ha, yuborish',
        'en': 'Yes, send',
    },
    'no': {
        'ru': 'Нет, изменить',
        'uz': "Yo'q, o'zgartirish",
        'en': 'No, change',
    },
    'no_file': {
        'ru': 'Нет файла',
        'uz': 'Fayl yo\'q',
        'en': 'No file',
    },
}

_ALLOWED_MIME = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}


@sync_to_async
def _save_application(data: dict) -> bool:
    try:
        from main.models import PartnerApplication
        PartnerApplication.objects.create(
            full_name=data.get('full_name', ''),
            company=data.get('company', ''),
            contact=data.get('contact', ''),
            offer_type=data.get('offer_type', 'other'),
            telegram_id=data.get('telegram_id'),
            status='new',
        )
        return True
    except Exception as exc:
        logger.error('PartnerApplication save error: %s', exc, exc_info=True)
        return False


@sync_to_async
def _save_application_with_file(data: dict, file_bytes: bytes, filename: str) -> bool:
    """Сохраняет заявку с файлом КП."""
    try:
        import io
        from django.core.files.base import ContentFile
        from main.models import PartnerApplication

        app = PartnerApplication(
            full_name=data.get('full_name', ''),
            company=data.get('company', ''),
            contact=data.get('contact', ''),
            offer_type=data.get('offer_type', 'other'),
            telegram_id=data.get('telegram_id'),
            status='new',
        )
        app.proposal_file.save(filename, ContentFile(file_bytes), save=True)
        return True
    except Exception as exc:
        logger.error('PartnerApplication save_with_file error: %s', exc, exc_info=True)
        return False


@sync_to_async
def _send_notify(data: dict, offer_type_display: str) -> None:
    """Уведомление в notify_chat_id — через _fire_and_forget не идёт, отдельный поток."""
    import threading
    from django.db import connection

    def _run():
        try:
            from main.services.telegram.bot_service import BotService
            config = BotService.get_config()
            if not config or not config.notify_chat_id:
                return

            import asyncio
            from aiogram import Bot
            from aiogram.client.default import DefaultBotProperties
            from aiogram.enums import ParseMode

            file_info = 'есть' if data.get('has_file') else 'нет'
            text = (
                f"🤝 <b>Новое партнёрское предложение</b>\n\n"
                f"Тип: <b>{offer_type_display}</b>\n"
                f"ФИО: <b>{data.get('full_name', '—')}</b>\n"
                f"Компания: <b>{data.get('company', '—')}</b>\n"
                f"Контакт: <b>{data.get('contact', '—')}</b>\n"
                f"Файл КП: <b>{file_info}</b>\n\n"
                f"<a href='/admin/main/partnerapplication/'>Открыть в Admin</a>"
            )

            async def _send():
                bot = Bot(
                    token=config.bot_token,
                    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
                )
                try:
                    await bot.send_message(
                        chat_id=config.notify_chat_id,
                        text=text,
                        disable_web_page_preview=True,
                    )
                finally:
                    await bot.session.close()

            asyncio.run(_send())
        except Exception as exc:
            logger.error('partner notify failed: %s', exc)
        finally:
            connection.close()

    threading.Thread(target=_run, daemon=True).start()



def _build_type_keyboard(lang: str) -> ReplyKeyboardMarkup:
    types = _OFFER_TYPES.get(lang, _OFFER_TYPES['ru'])
    rows = []
    row = []
    for _, label in types:
        row.append(KeyboardButton(text=label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=_TEXT['cancel'][lang])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _build_skip_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_TEXT['skip'][lang])],
            [KeyboardButton(text=_TEXT['cancel'][lang])],
        ],
        resize_keyboard=True,
    )


def _build_confirm_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_TEXT['yes'][lang])],
            [KeyboardButton(text=_TEXT['no'][lang])],
            [KeyboardButton(text=_TEXT['cancel'][lang])],
        ],
        resize_keyboard=True,
    )


def _get_offer_key(label: str, lang: str) -> str | None:
    for key, lbl in _OFFER_TYPES.get(lang, _OFFER_TYPES['ru']):
        if lbl == label:
            return key
    return None


def _get_offer_label(key: str, lang: str) -> str:
    for k, lbl in _OFFER_TYPES.get(lang, _OFFER_TYPES['ru']):
        if k == key:
            return lbl
    return key



@router.message(F.text.in_(PARTNER_TRIGGERS))
async def handle_partner_enter(
    message: Message,
    state: FSMContext,
    user: TelegramUser | None,
):
    lang = user.language if user else 'ru'
    await state.clear()
    await state.set_state(PartnerStates.choose_type)
    await state.update_data(language=lang)
    await message.answer(
        _TEXT['enter'][lang],
        reply_markup=_build_type_keyboard(lang),
    )


@router.message(PartnerStates.choose_type)
async def handle_partner_type(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    if message.text == _TEXT['cancel'][lang]:
        await state.clear()
        await message.answer(
            _TEXT['cancelled'][lang],
            reply_markup=await get_main_menu_keyboard(lang),
        )
        return

    offer_key = _get_offer_key(message.text or '', lang)
    if not offer_key:
        await message.answer(
            _TEXT['enter'][lang],
            reply_markup=_build_type_keyboard(lang),
        )
        return

    await state.update_data(offer_type=offer_key, offer_type_label=message.text)
    await state.set_state(PartnerStates.enter_name)
    await message.answer(
        _TEXT['ask_name'][lang],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=_TEXT['cancel'][lang])]],
            resize_keyboard=True,
        ),
    )


@router.message(PartnerStates.enter_name)
async def handle_partner_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    if message.text == _TEXT['cancel'][lang]:
        await state.clear()
        await message.answer(
            _TEXT['cancelled'][lang],
            reply_markup=await get_main_menu_keyboard(lang),
        )
        return

    name = (message.text or '').strip()
    if len(name) < 2:
        await message.answer(
            _TEXT['invalid_name'][lang],
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=_TEXT['cancel'][lang])]],
                resize_keyboard=True,
            ),
        )
        return

    await state.update_data(full_name=name)
    await state.set_state(PartnerStates.enter_company)
    await message.answer(
        _TEXT['ask_company'][lang],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=_TEXT['cancel'][lang])]],
            resize_keyboard=True,
        ),
    )


@router.message(PartnerStates.enter_company)
async def handle_partner_company(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    if message.text == _TEXT['cancel'][lang]:
        await state.clear()
        await message.answer(
            _TEXT['cancelled'][lang],
            reply_markup=await get_main_menu_keyboard(lang),
        )
        return

    company = (message.text or '').strip()
    if len(company) < 2:
        await message.answer(
            _TEXT['invalid_company'][lang],
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=_TEXT['cancel'][lang])]],
                resize_keyboard=True,
            ),
        )
        return

    await state.update_data(company=company)
    await state.set_state(PartnerStates.enter_contact)
    await message.answer(
        _TEXT['ask_contact'][lang],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=_TEXT['cancel'][lang])]],
            resize_keyboard=True,
        ),
    )


@router.message(PartnerStates.enter_contact)
async def handle_partner_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    if message.text == _TEXT['cancel'][lang]:
        await state.clear()
        await message.answer(
            _TEXT['cancelled'][lang],
            reply_markup=await get_main_menu_keyboard(lang),
        )
        return

    contact = (message.text or '').strip()
    is_phone    = contact.lstrip('+').replace(' ', '').replace('-', '').isdigit() and len(contact) >= 7
    is_telegram = contact.startswith('@') and len(contact) >= 3

    if not is_phone and not is_telegram:
        await message.answer(
            _TEXT['invalid_contact'][lang],
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=_TEXT['cancel'][lang])]],
                resize_keyboard=True,
            ),
        )
        return

    await state.update_data(contact=contact)
    await state.set_state(PartnerStates.upload_file)
    await message.answer(
        _TEXT['ask_file'][lang],
        reply_markup=_build_skip_keyboard(lang),
    )


@router.message(PartnerStates.upload_file)
async def handle_partner_file(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    if message.text == _TEXT['cancel'][lang]:
        await state.clear()
        await message.answer(
            _TEXT['cancelled'][lang],
            reply_markup=await get_main_menu_keyboard(lang),
        )
        return

    if message.text == _TEXT['skip'][lang]:
        await state.update_data(has_file=False, file_id=None, file_name=None)
        await _show_confirm(message, state, lang)
        return

    if message.document:
        doc: Document = message.document
        if doc.mime_type not in _ALLOWED_MIME:
            await message.answer(
                _TEXT['invalid_file'][lang],
                reply_markup=_build_skip_keyboard(lang),
            )
            return
        await state.update_data(
            has_file=True,
            file_id=doc.file_id,
            file_name=doc.file_name or 'proposal',
        )
        await _show_confirm(message, state, lang)
        return

    await message.answer(
        _TEXT['invalid_file'][lang],
        reply_markup=_build_skip_keyboard(lang),
    )


async def _show_confirm(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    file_display = data.get('file_name') if data.get('has_file') else _TEXT['no_file'][lang]
    text = _TEXT['confirm'][lang].format(
        offer_type=data.get('offer_type_label', '—'),
        full_name=data.get('full_name', '—'),
        company=data.get('company', '—'),
        contact=data.get('contact', '—'),
        file=file_display,
    )
    await state.set_state(PartnerStates.confirm)
    await message.answer(text, reply_markup=_build_confirm_keyboard(lang))


@router.message(PartnerStates.confirm)
async def handle_partner_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'ru')

    if message.text in (_TEXT['cancel'][lang], _TEXT['no'][lang]):
        await state.clear()
        await message.answer(
            _TEXT['cancelled'][lang],
            reply_markup=await get_main_menu_keyboard(lang),
        )
        return

    if message.text != _TEXT['yes'][lang]:
        await message.answer(
            _TEXT['confirm'][lang].format(
                offer_type=data.get('offer_type_label', '—'),
                full_name=data.get('full_name', '—'),
                company=data.get('company', '—'),
                contact=data.get('contact', '—'),
                file=data.get('file_name') if data.get('has_file') else _TEXT['no_file'][lang],
            ),
            reply_markup=_build_confirm_keyboard(lang),
        )
        return

    save_data = {
        'full_name':    data.get('full_name', ''),
        'company':      data.get('company', ''),
        'contact':      data.get('contact', ''),
        'offer_type':   data.get('offer_type', 'other'),
        'telegram_id':  message.from_user.id,
        'has_file':     data.get('has_file', False),
    }

    if data.get('has_file') and data.get('file_id'):
        try:
            from aiogram import Bot
            bot: Bot = message.bot
            file      = await bot.get_file(data['file_id'])
            file_bytes = await bot.download_file(file.file_path)
            content    = file_bytes.read() if hasattr(file_bytes, 'read') else bytes(file_bytes)
            ok = await _save_application_with_file(
                save_data,
                content,
                data.get('file_name', 'proposal'),
            )
        except Exception as exc:
            logger.error('partner file download failed: %s', exc, exc_info=True)
            ok = await _save_application(save_data)
    else:
        ok = await _save_application(save_data)

    await state.clear()
    main_menu = await get_main_menu_keyboard(lang)

    if ok:
        offer_label = _get_offer_label(data.get('offer_type', 'other'), lang)
        await _send_notify({**save_data}, offer_label)
        await message.answer(
            _TEXT['success'][lang],
            reply_markup=main_menu,
        )
        logger.info(
            'PartnerApplication saved: telegram_id=%s company=%s type=%s',
            message.from_user.id, data.get('company'), data.get('offer_type'),
        )
    else:
        await message.answer(_TEXT['error'][lang], reply_markup=main_menu)