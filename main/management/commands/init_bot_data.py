from django.core.management.base import BaseCommand
from main.models import BotMessage, BotMenuItem


BOT_MESSAGES = [
    {
        'key': 'welcome_back',
        'description': 'Приветствие вернувшегося пользователя',
        'texts': {
            'ru': 'Добро пожаловать, <b>{name}</b>!\n\nЧем могу помочь?',
            'uz': 'Xush kelibsiz, <b>{name}</b>!\n\nNima bilan yordam bera olaman?',
            'en': 'Welcome back, <b>{name}</b>!\n\nHow can I help you?',
        },
    },
    {
        'key': 'language_changed',
        'description': 'Язык изменён',
        'texts': {
            'ru': 'Язык изменён. Главное меню:',
            'uz': 'Til o\'zgartirildi. Asosiy menyu:',
            'en': 'Language changed. Main menu:',
        },
    },

    # ─── Регистрация ───────────────────────────────────────────────────────
    {
        'key': 'enter_first_name',
        'description': 'Запрос имени при регистрации',
        'texts': {
            'ru': 'Введите ваше имя:',
            'uz': 'Ismingizni kiriting:',
            'en': 'Enter your first name:',
        },
    },
    {
        'key': 'enter_last_name',
        'description': 'Запрос фамилии при регистрации',
        'texts': {
            'ru': 'Введите вашу фамилию:',
            'uz': 'Familiyangizni kiriting:',
            'en': 'Enter your last name:',
        },
    },
    {
        'key': 'enter_age',
        'description': 'Запрос возраста при регистрации',
        'texts': {
            'ru': 'Введите ваш возраст:',
            'uz': 'Yoshingizni kiriting:',
            'en': 'Enter your age:',
        },
    },
    {
        'key': 'choose_region',
        'description': 'Выбор региона при регистрации',
        'texts': {
            'ru': 'Выберите ваш регион:',
            'uz': 'Viloyatingizni tanlang:',
            'en': 'Choose your region:',
        },
    },
    {
        'key': 'enter_phone',
        'description': 'Запрос телефона при регистрации',
        'texts': {
            'ru': (
                'Отправьте ваш номер телефона.\n\n'
                'Нажмите кнопку <b>Поделиться номером</b> '
                'или введите вручную в формате <b>+998XXXXXXXXX</b>'
            ),
            'uz': (
                'Telefon raqamingizni yuboring.\n\n'
                '<b>Raqamni ulashish</b> tugmasini bosing '
                'yoki <b>+998XXXXXXXXX</b> formatida kiriting'
            ),
            'en': (
                'Send your phone number.\n\n'
                'Press <b>Share number</b> button '
                'or enter manually in format <b>+998XXXXXXXXX</b>'
            ),
        },
    },
    {
        'key': 'enter_phone_manually_hint',
        'description': 'Подсказка при ручном вводе телефона',
        'texts': {
            'ru': 'Введите номер в формате <b>+998XXXXXXXXX</b>:',
            'uz': '<b>+998XXXXXXXXX</b> formatida raqam kiriting:',
            'en': 'Enter number in format <b>+998XXXXXXXXX</b>:',
        },
    },
    {
        'key': 'registration_complete',
        'description': 'Успешная регистрация',
        'texts': {
            'ru': (
                '<b>{name}</b>, регистрация завершена!\n\n'
                'Теперь вы можете пользоваться всеми функциями бота.'
            ),
            'uz': (
                '<b>{name}</b>, royxatdan otish yakunlandi!\n\n'
                'Endi botning barcha imkoniyatlaridan foydalanishingiz mumkin.'
            ),
            'en': (
                '<b>{name}</b>, registration complete!\n\n'
                'You can now use all bot features.'
            ),
        },
    },

    # ─── Ошибки валидации ──────────────────────────────────────────────────
    {
        'key': 'invalid_name',
        'description': 'Ошибка валидации имени/фамилии',
        'texts': {
            'ru': (
                'Некорректное имя.\n\n'
                'Используйте только буквы, от 2 до 50 символов.'
            ),
            'uz': (
                'Noto\'g\'ri ism.\n\n'
                'Faqat harflar, 2 dan 50 gacha belgi.'
            ),
            'en': (
                'Invalid name.\n\n'
                'Use letters only, 2 to 50 characters.'
            ),
        },
    },
    {
        'key': 'invalid_age',
        'description': 'Ошибка валидации возраста',
        'texts': {
            'ru': 'Введите корректный возраст (от 16 до 90):',
            'uz': 'To\'g\'ri yosh kiriting (16 dan 90 gacha):',
            'en': 'Enter a valid age (16 to 90):',
        },
    },
    {
        'key': 'invalid_phone',
        'description': 'Ошибка валидации телефона',
        'texts': {
            'ru': 'Неверный формат. Введите номер в формате <b>+998XXXXXXXXX</b>:',
            'uz': 'Noto\'g\'ri format. <b>+998XXXXXXXXX</b> formatida kiriting:',
            'en': 'Invalid format. Enter number as <b>+998XXXXXXXXX</b>:',
        },
    },
    {
        'key': 'phone_own_only',
        'description': 'Попытка поделиться чужим контактом',
        'texts': {
            'ru': 'Пожалуйста, отправьте только свой номер телефона.',
            'uz': 'Iltimos, faqat o\'z telefon raqamingizni yuboring.',
            'en': 'Please share only your own phone number.',
        },
    },
    {
        'key': 'choose_from_list',
        'description': 'Просьба выбрать из списка',
        'texts': {
            'ru': 'Пожалуйста, выберите из списка.',
            'uz': 'Iltimos, ro\'yxatdan tanlang.',
            'en': 'Please choose from the list.',
        },
    },

    # ─── Каталог ───────────────────────────────────────────────────────────
    {
        'key': 'catalog_choose_category',
        'description': 'Выбор категории в каталоге',
        'texts': {
            'ru': 'Выберите категорию:',
            'uz': 'Kategoriyani tanlang:',
            'en': 'Choose category:',
        },
    },
    {
        'key': 'catalog_choose_product',
        'description': 'Выбор модели в каталоге',
        'texts': {
            'ru': 'Выберите модель:',
            'uz': 'Modelni tanlang:',
            'en': 'Choose model:',
        },
    },
    {
        'key': 'catalog_no_products',
        'description': 'Нет продуктов в категории',
        'texts': {
            'ru': 'В этой категории пока нет автомобилей.',
            'uz': 'Bu kategoriyada hozircha avtomobillar yo\'q.',
            'en': 'No vehicles in this category yet.',
        },
    },
    {
        'key': 'catalog_more_info',
        'description': 'Кнопка подробнее на сайте',
        'texts': {
            'ru': 'Подробнее на сайте',
            'uz': 'Saytda batafsil',
            'en': 'More details on website',
        },
    },
    {
        'key': 'catalog_book_test_drive',
        'description': 'Кнопка записи на тест-драйв из карточки',
        'texts': {
            'ru': 'Записаться на тест-драйв',
            'uz': 'Test-drayvga yozilish',
            'en': 'Book test drive',
        },
    },
    {
        'key': 'catalog_add_wishlist',
        'description': 'Кнопка добавить в избранное',
        'texts': {
            'ru': 'В избранное',
            'uz': 'Sevimlilar',
            'en': 'Add to favorites',
        },
    },
    {
        'key': 'catalog_added_wishlist',
        'description': 'Добавлено в избранное',
        'texts': {
            'ru': 'Добавлено в избранное.',
            'uz': 'Sevimlilarga qo\'shildi.',
            'en': 'Added to favorites.',
        },
    },
    {
        'key': 'catalog_removed_wishlist',
        'description': 'Убрано из избранного',
        'texts': {
            'ru': 'Убрано из избранного.',
            'uz': 'Sevimlilardan olib tashlandi.',
            'en': 'Removed from favorites.',
        },
    },


    {
        'key': 'dealers_title',
        'description': 'Заголовок раздела дилеров',
        'texts': {
            'ru': '<b>Дилерские центры FAW</b>\n\nВыберите дилера:',
            'uz': '<b>FAW Dilerlik markazlari</b>\n\nDilerni tanlang:',
            'en': '<b>FAW Dealerships</b>\n\nChoose a dealer:',
        },
    },
    {
        'key': 'dealers_no_dealers',
        'description': 'Нет дилеров',
        'texts': {
            'ru': 'Информация о дилерских центрах скоро появится.',
            'uz': 'Dilerlik markazlari haqida ma\'lumot tez orada qo\'shiladi.',
            'en': 'Dealership information will be available soon.',
        },
    },
    {
        'key': 'dealers_open_map',
        'description': 'Кнопка открыть на карте',
        'texts': {
            'ru': 'Открыть на карте',
            'uz': 'Xaritada ochish',
            'en': 'Open on map',
        },
    },

    # ─── Тест-драйв ────────────────────────────────────────────────────────
    {
        'key': 'td_choose_dealer',
        'description': 'Выбор дилера для тест-драйва',
        'texts': {
            'ru': 'Выберите дилерский центр:',
            'uz': 'Dilerlik markazini tanlang:',
            'en': 'Choose a dealership:',
        },
    },
    {
        'key': 'td_choose_product',
        'description': 'Выбор модели для тест-драйва',
        'texts': {
            'ru': 'Выберите модель автомобиля:',
            'uz': 'Avtomobil modelini tanlang:',
            'en': 'Choose a car model:',
        },
    },
    {
        'key': 'td_choose_date',
        'description': 'Выбор даты тест-драйва',
        'texts': {
            'ru': 'Выберите удобную дату:',
            'uz': 'Qulay sanani tanlang:',
            'en': 'Choose a convenient date:',
        },
    },
    {
        'key': 'td_choose_time',
        'description': 'Выбор времени тест-драйва',
        'texts': {
            'ru': 'Выберите удобное время:',
            'uz': 'Qulay vaqtni tanlang:',
            'en': 'Choose a convenient time:',
        },
    },
    {
        'key': 'td_confirm',
        'description': 'Подтверждение тест-драйва',
        'texts': {
            'ru': (
                '<b>Ваша заявка на тест-драйв:</b>\n\n'
                'Дилер: <b>{dealer}</b>\n'
                'Модель: <b>{product}</b>\n'
                'Дата: <b>{date}</b>\n'
                'Время: <b>{time}</b>\n'
                'Имя: <b>{name}</b>\n'
                'Телефон: <b>{phone}</b>\n\n'
                'Всё верно?'
            ),
            'uz': (
                '<b>Test-drayv uchun arizangiz:</b>\n\n'
                'Diler: <b>{dealer}</b>\n'
                'Model: <b>{product}</b>\n'
                'Sana: <b>{date}</b>\n'
                'Vaqt: <b>{time}</b>\n'
                'Ism: <b>{name}</b>\n'
                'Telefon: <b>{phone}</b>\n\n'
                'Hammasi to\'g\'rimi?'
            ),
            'en': (
                '<b>Your test drive request:</b>\n\n'
                'Dealer: <b>{dealer}</b>\n'
                'Model: <b>{product}</b>\n'
                'Date: <b>{date}</b>\n'
                'Time: <b>{time}</b>\n'
                'Name: <b>{name}</b>\n'
                'Phone: <b>{phone}</b>\n\n'
                'Is everything correct?'
            ),
        },
    },
    {
        'key': 'td_success',
        'description': 'Успешная запись на тест-драйв',
        'texts': {
            'ru': (
                'Вы успешно записаны на тест-драйв!\n\n'
                'Мы свяжемся с вами для подтверждения.'
            ),
            'uz': (
                'Siz muvaffaqiyatli test-drayvga yozildingiz!\n\n'
                'Tasdiqlash uchun siz bilan bog\'lanamiz.'
            ),
            'en': (
                'You have successfully booked a test drive!\n\n'
                'We will contact you for confirmation.'
            ),
        },
    },
    {
        'key': 'td_daily_limit',
        'description': 'Превышен дневной лимит заявок',
        'texts': {
            'ru': 'Вы уже отправили 2 заявки сегодня. Попробуйте завтра.',
            'uz': 'Siz bugun allaqachon 2 ta ariza yubordingiz. Ertaga urinib ko\'ring.',
            'en': 'You have already sent 2 requests today. Please try tomorrow.',
        },
    },
    {
        'key': 'td_no_dealers',
        'description': 'Нет дилеров для тест-драйва',
        'texts': {
            'ru': 'Дилерские центры пока не добавлены. Попробуйте позже.',
            'uz': 'Dilerlik markazlari hali qo\'shilmagan. Keyinroq urinib ko\'ring.',
            'en': 'No dealerships added yet. Please try later.',
        },
    },
    {
        'key': 'td_error',
        'description': 'Ошибка при создании заявки',
        'texts': {
            'ru': 'Произошла ошибка. Пожалуйста, попробуйте ещё раз.',
            'uz': 'Xatolik yuz berdi. Iltimos, qayta urinib ko\'ring.',
            'en': 'An error occurred. Please try again.',
        },
    },

    {
        'key': 'td_reminder',
        'description': 'Напоминание о тест-драйве за день до',
        'texts': {
            'ru': (
                'Здравствуйте, <b>{name}</b>!\n\n'
                'Напоминаем: завтра у вас тест-драйв.\n\n'
                'Дата: <b>{date}</b>\n'
                'Время: <b>{time}</b>\n'
                'Дилер: <b>{dealer}</b>\n\n'
                'Ждём вас!'
            ),
            'uz': (
                'Salom, <b>{name}</b>!\n\n'
                'Eslatma: ertaga sizda test-drayv bor.\n\n'
                'Sana: <b>{date}</b>\n'
                'Vaqt: <b>{time}</b>\n'
                'Diler: <b>{dealer}</b>\n\n'
                'Sizni kutamiz!'
            ),
            'en': (
                'Hello, <b>{name}</b>!\n\n'
                'Reminder: you have a test drive tomorrow.\n\n'
                'Date: <b>{date}</b>\n'
                'Time: <b>{time}</b>\n'
                'Dealer: <b>{dealer}</b>\n\n'
                'We look forward to seeing you!'
            ),
        },
    },

    {
        'key': 'lead_choose_interest',
        'description': 'Выбор интереса при оставлении заявки',
        'texts': {
            'ru': 'Что вас интересует?',
            'uz': 'Sizni nima qiziqtiradi?',
            'en': 'What are you interested in?',
        },
    },
    {
        'key': 'lead_success',
        'description': 'Заявка успешно отправлена',
        'texts': {
            'ru': 'Ваша заявка принята! Менеджер свяжется с вами в ближайшее время.',
            'uz': 'Arizangiz qabul qilindi! Menejer tez orada siz bilan bog\'lanadi.',
            'en': 'Your request has been received! A manager will contact you shortly.',
        },
    },
    {
        'key': 'lead_error',
        'description': 'Ошибка при отправке заявки',
        'texts': {
            'ru': 'Не удалось отправить заявку. Попробуйте ещё раз.',
            'uz': 'Ariza yuborib bo\'lmadi. Yana urinib ko\'ring.',
            'en': 'Failed to send request. Please try again.',
        },
    },

    # ─── FAQ ───────────────────────────────────────────────────────────────
    {
        'key': 'faq_title',
        'description': 'Заголовок раздела FAQ',
        'texts': {
            'ru': 'Часто задаваемые вопросы.\n\nВыберите вопрос:',
            'uz': 'Ko\'p so\'raladigan savollar.\n\nSavolni tanlang:',
            'en': 'Frequently asked questions.\n\nChoose a question:',
        },
    },
    {
        'key': 'faq_empty',
        'description': 'FAQ пуст',
        'texts': {
            'ru': 'Раздел FAQ пока пуст.',
            'uz': 'FAQ bo\'limi hali to\'ldirilmagan.',
            'en': 'FAQ section is empty for now.',
        },
    },

    # ─── Профиль ───────────────────────────────────────────────────────────
    {
        'key': 'profile_title',
        'description': 'Заголовок профиля',
        'texts': {
            'ru': (
                '<b>Ваш профиль</b>\n\n'
                'Имя: {first_name}\n'
                'Фамилия: {last_name}\n'
                'Возраст: {age}\n'
                'Регион: {region}\n'
                'Телефон: {phone}\n'
                'Язык: {language}\n'
                'Заявок: {total_requests}'
            ),
            'uz': (
                '<b>Sizning profilingiz</b>\n\n'
                'Ism: {first_name}\n'
                'Familiya: {last_name}\n'
                'Yosh: {age}\n'
                'Viloyat: {region}\n'
                'Telefon: {phone}\n'
                'Til: {language}\n'
                'Arizalar: {total_requests}'
            ),
            'en': (
                '<b>Your profile</b>\n\n'
                'First name: {first_name}\n'
                'Last name: {last_name}\n'
                'Age: {age}\n'
                'Region: {region}\n'
                'Phone: {phone}\n'
                'Language: {language}\n'
                'Requests: {total_requests}'
            ),
        },
    },

    # ─── Новости ───────────────────────────────────────────────────────────
    {
        'key': 'news_title',
        'description': 'Заголовок раздела новостей',
        'texts': {
            'ru': '<b>Новости FAW</b>\n\nПоследние новости:',
            'uz': '<b>FAW Yangiliklari</b>\n\nSo\'nggi yangiliklar:',
            'en': '<b>FAW News</b>\n\nLatest news:',
        },
    },
    {
        'key': 'news_empty',
        'description': 'Нет новостей',
        'texts': {
            'ru': 'Новостей пока нет.',
            'uz': 'Yangiliklar hali yo\'q.',
            'en': 'No news yet.',
        },
    },
    {
        'key': 'promotions_title',
        'description': 'Заголовок раздела акций',
        'texts': {
            'ru': '<b>Акции и специальные предложения</b>',
            'uz': '<b>Aksiyalar va maxsus takliflar</b>',
            'en': '<b>Promotions and special offers</b>',
        },
    },
    {
        'key': 'promotions_empty',
        'description': 'Нет активных акций',
        'texts': {
            'ru': 'Активных акций нет. Следите за обновлениями!',
            'uz': 'Faol aksiyalar yo\'q. Yangilanishlarni kuzatib boring!',
            'en': 'No active promotions. Stay tuned for updates!',
        },
    },

    # ─── Общие ─────────────────────────────────────────────────────────────
    {
        'key': 'main_menu_text',
        'description': 'Текст над главным меню',
        'texts': {
            'ru': 'Главное меню. Выберите раздел:',
            'uz': 'Asosiy menyu. Bo\'limni tanlang:',
            'en': 'Main menu. Choose a section:',
        },
    },
    {
        'key': 'unsupported_message',
        'description': 'Неподдерживаемый тип сообщения',
        'texts': {
            'ru': 'Пожалуйста, используйте кнопки меню.',
            'uz': 'Iltimos, menyu tugmalaridan foydalaning.',
            'en': 'Please use the menu buttons.',
        },
    },
    {
        'key': 'outside_working_hours',
        'description': 'Вне рабочего времени',
        'texts': {
            'ru': (
                'Мы работаем с 9:00 до 18:00 по Ташкенту.\n\n'
                'Ваш запрос записан — менеджер ответит в рабочее время.'
            ),
            'uz': (
                'Biz Toshkent bo\'yicha 9:00 dan 18:00 gacha ishlaymiz.\n\n'
                'So\'rovingiz qayd etildi — menejer ish vaqtida javob beradi.'
            ),
            'en': (
                'We work from 9:00 to 18:00 Tashkent time.\n\n'
                'Your request is noted — a manager will respond during working hours.'
            ),
        },
    },
]


BOT_MENU_ITEMS = [
    {
        'key': 'catalog',
        'label_ru': 'Каталог',
        'label_uz': 'Katalog',
        'label_en': 'Catalog',
        'emoji': '',
        'order': 1,
    },
    {
        'key': 'dealers',
        'label_ru': 'Дилеры',
        'label_uz': 'Dilerlar',
        'label_en': 'Dealers',
        'emoji': '',
        'order': 2,
    },
    {
        'key': 'news',
        'label_ru': 'Новости',
        'label_uz': 'Yangiliklar',
        'label_en': 'News',
        'emoji': '',
        'order': 3,
    },
    {
        'key': 'promotions',
        'label_ru': 'Акции',
        'label_uz': 'Aksiyalar',
        'label_en': 'Promotions',
        'emoji': '',
        'order': 4,
    },
    {
        'key': 'test_drive',
        'label_ru': 'Тест-драйв',
        'label_uz': 'Test-drayv',
        'label_en': 'Test drive',
        'emoji': '',
        'order': 5,
    },
    {
        'key': 'lead',
        'label_ru': 'Оставить заявку',
        'label_uz': 'Ariza qoldirish',
        'label_en': 'Leave a request',
        'emoji': '',
        'order': 6,
    },
    {
        'key': 'leasing',
        'label_ru': 'Лизинг',
        'label_uz': 'Lizing',
        'label_en': 'Leasing',
        'emoji': '',
        'order': 7,
    },
    {
        'key': 'faq',
        'label_ru': 'Вопросы и ответы',
        'label_uz': 'Savol va javoblar',
        'label_en': 'FAQ',
        'emoji': '',
        'order': 8,
    },
    {
        'key': 'contacts',
        'label_ru': 'Контакты',
        'label_uz': 'Kontaktlar',
        'label_en': 'Contacts',
        'emoji': '',
        'order': 9,
    },
    {
        'key': 'profile',
        'label_ru': 'Мой профиль',
        'label_uz': 'Mening profilim',
        'label_en': 'My profile',
        'emoji': '',
        'order': 10,
    },
    {
        'key': 'language',
        'label_ru': 'Сменить язык',
        'label_uz': 'Tilni o\'zgartirish',
        'label_en': 'Change language',
        'emoji': '',
        'order': 11,
    },
]


class Command(BaseCommand):
    help = 'Заполнение начальных данных для Telegram бота'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help='Принудительно обновить существующие записи',
        )

    def handle(self, *args, **options):
        force = options['force']
        self._create_messages(force)
        self._create_menu_items(force)
        self.stdout.write(self.style.SUCCESS('Bot data initialized successfully.'))

    def _create_messages(self, force: bool) -> None:
        created_count = 0
        updated_count = 0

        for item in BOT_MESSAGES:
            key = item['key']
            description = item['description']

            for lang, text in item['texts'].items():
                if force:
                    _, created = BotMessage.objects.update_or_create(
                        key=key,
                        language=lang,
                        defaults={'text': text, 'description': description},
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                else:
                    _, created = BotMessage.objects.get_or_create(
                        key=key,
                        language=lang,
                        defaults={'text': text, 'description': description},
                    )
                    if created:
                        created_count += 1

        self.stdout.write(
            f'BotMessages: {created_count} created, {updated_count} updated.'
        )

    def _create_menu_items(self, force: bool) -> None:
        created_count = 0
        updated_count = 0

        for item in BOT_MENU_ITEMS:
            key = item['key']
            defaults = {k: v for k, v in item.items() if k != 'key'}

            if force:
                _, created = BotMenuItem.objects.update_or_create(
                    key=key,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            else:
                _, created = BotMenuItem.objects.get_or_create(
                    key=key,
                    defaults=defaults,
                )
                if created:
                    created_count += 1

        self.stdout.write(
            f'BotMenuItems: {created_count} created, {updated_count} updated.'
        )
        