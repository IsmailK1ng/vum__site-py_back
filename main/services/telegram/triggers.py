"""
Триггеры кнопок главного меню.

Раньше здесь лежали захардкоженные frozenset со строками кнопок
('Каталог', 'Katalog', 'Catalog', ...). Проблема: подписи кнопок
(BotMenuItem.label_ru/uz/en) редактируются в Django Admin, а эти
frozenset — нет. Правка подписи в админке молча ломала роутинг:
хендлер переставал узнавать кнопку, без единой ошибки в логах.

Теперь MenuTrigger — это aiogram-фильтр, который на каждое сообщение
спрашивает у BotService.get_menu_item_labels(key) актуальные подписи
по стабильному key (BotMenuItem.KEY_CHOICES), а не по тексту. Правка
label_* в админке сразу (в пределах TTL кеша — 5 минут, см.
_MSG_CACHE_TTL) отражается на роутинге без деплоя.
"""
from aiogram.filters import BaseFilter
from aiogram.types import Message
from asgiref.sync import sync_to_async

from main.services.telegram.bot_service import BotService


@sync_to_async
def _get_labels(key: str) -> frozenset:
    return BotService.get_menu_item_labels(key)


class MenuTrigger(BaseFilter):
    def __init__(self, key: str):
        self.key = key

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        labels = await _get_labels(self.key)
        return message.text in labels


LANGUAGE_TRIGGERS = MenuTrigger('language')
PROFILE_TRIGGERS = MenuTrigger('profile')
CATALOG_TRIGGERS = MenuTrigger('catalog')
TD_TRIGGERS = MenuTrigger('test_drive')
LEASING_TRIGGERS = MenuTrigger('leasing')
CONTACTS_TRIGGERS = MenuTrigger('contacts')
NEWS_TRIGGERS = MenuTrigger('news')
PROMOTIONS_TRIGGERS = MenuTrigger('promotions')
DEALERS_TRIGGERS = MenuTrigger('dealers')
FAQ_TRIGGERS = MenuTrigger('faq')
LEAD_TRIGGERS = MenuTrigger('lead')
PARTNER_TRIGGERS = MenuTrigger('partner')
