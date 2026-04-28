from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

BUTTON_LABELS = {
    'ru': {
        'back':                 'Назад',
        'main_menu':            'Главное меню',
        'yes':                  'Да, верно',
        'no':                   'Нет, изменить',
        'share_phone':          'Поделиться номером',
        'enter_phone_manually': 'Ввести другой номер',
        'skip':                 'Пропустить',
    },
    'uz': {
        'back':                 'Orqaga',
        'main_menu':            'Asosiy menyu',
        'yes':                  'Ha, togri',
        'no':                   "Yoq, ozgartirish",
        'share_phone':          'Raqamni ulashish',
        'enter_phone_manually': 'Boshqa raqam kiritish',
        'skip':                 'Otkazib yuborish',
    },
    'en': {
        'back':                 'Back',
        'main_menu':            'Main menu',
        'yes':                  'Yes, correct',
        'no':                   'No, change',
        'share_phone':          'Share number',
        'enter_phone_manually': 'Enter different number',
        'skip':                 'Skip',
    },
}


def get_button_labels(language: str) -> dict:
    return BUTTON_LABELS.get(language, BUTTON_LABELS['ru'])


def get_back_keyboard(language: str) -> ReplyKeyboardMarkup:
    label = get_button_labels(language)['back']
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)]],
        resize_keyboard=True,
    )


def get_confirm_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = get_button_labels(language)
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=labels['yes']),
                KeyboardButton(text=labels['no']),
            ],
            [KeyboardButton(text=labels['back'])],
        ],
        resize_keyboard=True,
    )


def get_phone_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = get_button_labels(language)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text=labels['share_phone'],
                request_contact=True,
            )],
            [KeyboardButton(text=labels['enter_phone_manually'])],
            [KeyboardButton(text=labels['back'])],
        ],
        resize_keyboard=True,
    )


def get_language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Русский'),
                KeyboardButton(text="O'zbekcha"),
            ],
            [KeyboardButton(text='English')],
        ],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()