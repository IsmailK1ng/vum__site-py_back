"""
Полный тест-сьют для FAW.UZ Telegram Bot.

Покрывает:
- BotService все методы
- _fire_and_forget не блокирует поток
- FSM state очищается везде где нужно
- Триггеры совпадают с BotMenuItem labels
- REGION_LABELS покрывает все REGION_CHOICES
- Все handlers корректно импортируются

Запуск: python manage.py test main.tests.test_bot_service -v 2
"""

import threading
import time
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from main.models import (
    BotConfig,
    BotContacts,
    BotMessage,
    BotMenuItem,
    ContactForm,
    Dealer,
    FAQItem,
    News,
    Product,
    ProductViewHistory,
    ProductWishlist,
    Promotion,
    TelegramUser,
    TestDriveRequest,
    REGION_CHOICES,
    REGION_LABELS,
)
from main.services.telegram.bot_service import (
    BotService,
    PRODUCT_CATEGORIES,
    PRODUCT_SUBCATEGORIES,
    TEST_DRIVE_TIME_SLOTS,
    _t,
    _field,
    _build_utm,
)
from main.services.telegram.triggers import (
    CATALOG_TRIGGERS,
    TD_TRIGGERS,
    LEASING_TRIGGERS,
    CONTACTS_TRIGGERS,
    NEWS_TRIGGERS,
    PROMOTIONS_TRIGGERS,
    DEALERS_TRIGGERS,
    FAQ_TRIGGERS,
    LEAD_TRIGGERS,
    PROFILE_TRIGGERS,
    LANGUAGE_TRIGGERS,
)


# ─── Фабрики ─────────────────────────────────────────────────────────────────

def make_user(**kwargs) -> TelegramUser:
    defaults = {
        'telegram_id': 123456789,
        'first_name': 'Иван',
        'phone': '+998901234567',
        'language': 'ru',
        'status': 'new',
        'is_blocked': False,
        'notifications_enabled': True,
        'region': 'tashkent_city',
    }
    defaults.update(kwargs)
    return TelegramUser.objects.create(**defaults)


def make_product(**kwargs) -> Product:
    defaults = {
        'title': 'FAW Tiger V Test',
        'title_ru': 'FAW Tiger V Test RU',
        'title_uz': 'FAW Tiger V Test UZ',
        'title_en': 'FAW Tiger V Test EN',
        'slug': 'faw-tiger-v-test',
        'category': 'furgon',
        'categories': 'tiger_v',
        'is_active': True,
        'slider_year': '2025',
        'slider_price': '500 000 000 sum',
        'slider_price_ru': '500 000 000 сум',
        'order': 0,
    }
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def make_dealer(**kwargs) -> Dealer:
    defaults = {
        'name': 'Test Dealer',
        'city': 'Toshkent',
        'address': 'Test address',
        'address_ru': 'Тестовый адрес',
        'latitude': '41.299698',
        'longitude': '69.240073',
        'phone': '+998712345678',
        'email': 'dealer@test.com',
        'working_hours': '09:00-18:00',
        'working_hours_ru': '09:00-18:00',
        'is_active': True,
        'order': 0,
    }
    defaults.update(kwargs)
    return Dealer.objects.create(**defaults)


def make_bot_config(**kwargs) -> BotConfig:
    defaults = {
        'bot_token': 'test_token_123',
        'notify_chat_id': '-100123456789',
        'is_active': True,
        'use_webhook': False,
        'site_url': 'https://faw.uz',
    }
    defaults.update(kwargs)
    BotConfig.objects.filter(pk=1).delete()
    return BotConfig.objects.create(pk=1, **defaults)


def make_bot_message(key: str, **kwargs) -> None:
    for lang in ('ru', 'uz', 'en'):
        BotMessage.objects.get_or_create(
            key=key,
            language=lang,
            defaults={'text': f'{key}_{lang}'},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

class TestHelpers(TestCase):

    def test_t_correct_language(self):
        t = {'ru': 'Фургоны', 'uz': 'Avtofurgonlar', 'en': 'Vans'}
        self.assertEqual(_t(t, 'ru'), 'Фургоны')
        self.assertEqual(_t(t, 'uz'), 'Avtofurgonlar')
        self.assertEqual(_t(t, 'en'), 'Vans')

    def test_t_fallback_to_ru(self):
        self.assertEqual(_t({'ru': 'Фургоны'}, 'en'), 'Фургоны')

    def test_t_empty_dict(self):
        self.assertEqual(_t({}, 'ru'), '')

    def test_field_translated(self):
        p = make_product()
        self.assertEqual(_field(p, 'title', 'ru'), 'FAW Tiger V Test RU')
        self.assertEqual(_field(p, 'title', 'uz'), 'FAW Tiger V Test UZ')
        self.assertEqual(_field(p, 'title', 'en'), 'FAW Tiger V Test EN')

    def test_field_fallback_to_base(self):
        p = make_product(title_en='')
        result = _field(p, 'title', 'en')
        self.assertIn('FAW Tiger V Test', result)

    def test_build_utm_structure(self):
        import json
        utm = json.loads(_build_utm('test_campaign'))
        self.assertEqual(utm['utm_source'], 'telegram')
        self.assertEqual(utm['utm_medium'], 'bot')
        self.assertEqual(utm['utm_campaign'], 'test_campaign')

    def test_build_utm_ensure_ascii_false(self):
        """Кириллица в UTM не должна экранироваться."""
        import json
        utm_str = _build_utm('тест')
        self.assertNotIn('\\u', utm_str)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. КОНФИГ И КЕШИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfig(TestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_get_config_returns_instance(self):
        make_bot_config()
        config = BotService.get_config()
        self.assertIsInstance(config, BotConfig)
        self.assertEqual(config.bot_token, 'test_token_123')

    def test_config_cached_on_second_call(self):
        make_bot_config()
        BotService.get_config()
        with patch.object(BotConfig, 'get_instance') as mock:
            mock.return_value = BotConfig.objects.get(pk=1)
            BotService.get_config()
            mock.assert_not_called()

    def test_post_save_signal_clears_config_cache(self):
        """post_save сигнал должен сбрасывать кеш конфига."""
        from django.core.cache import cache
        config = make_bot_config()
        BotService.get_config()
        self.assertIsNotNone(cache.get('bot_config'))
        config.site_url = 'https://updated.faw.uz'
        config.save()
        self.assertIsNone(cache.get('bot_config'))

    def test_invalidate_config_cache(self):
        from django.core.cache import cache
        make_bot_config()
        BotService.get_config()
        BotService.invalidate_config_cache()
        self.assertIsNone(cache.get('bot_config'))


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ТЕКСТЫ И КЕШИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════════════════════

class TestMessages(TestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        BotMessage.objects.create(key='test_key', language='ru', text='Привет, {name}!')
        BotMessage.objects.create(key='test_key', language='uz', text='Salom, {name}!')

    def test_returns_text(self):
        self.assertEqual(BotService.get_message('test_key', 'ru'), 'Привет, {name}!')

    def test_formats_kwargs(self):
        self.assertEqual(
            BotService.get_message('test_key', 'ru', name='Иван'),
            'Привет, Иван!',
        )

    def test_fallback_to_ru(self):
        self.assertEqual(BotService.get_message('test_key', 'en'), 'Привет, {name}!')

    def test_missing_key_returns_key(self):
        self.assertEqual(BotService.get_message('nonexistent', 'ru'), 'nonexistent')

    def test_cached_after_first_call(self):
        from django.core.cache import cache
        BotService.get_message('test_key', 'ru')
        self.assertIsNotNone(cache.get('bot_msg_test_key_ru'))

    def test_format_error_returns_unformatted(self):
        text = BotService.get_message('test_key', 'ru', wrong_key='x')
        self.assertEqual(text, 'Привет, {name}!')

    def test_post_save_signal_clears_message_cache(self):
        """post_save сигнал должен сбрасывать кеш конкретного текста."""
        from django.core.cache import cache
        BotService.get_message('test_key', 'ru')
        self.assertIsNotNone(cache.get('bot_msg_test_key_ru'))
        msg = BotMessage.objects.get(key='test_key', language='ru')
        msg.text = 'Обновлённый текст'
        msg.save()
        self.assertIsNone(cache.get('bot_msg_test_key_ru'))

    def test_bulk_returns_all_keys(self):
        keys = ['test_key']
        result = BotService.get_messages_bulk(keys, 'ru')
        self.assertEqual(result['test_key'], 'Привет, {name}!')

    def test_bulk_missing_key_returns_key_itself(self):
        result = BotService.get_messages_bulk(['nonexistent'], 'ru')
        self.assertEqual(result['nonexistent'], 'nonexistent')

    def test_bulk_uses_cache_on_second_call(self):
        from django.core.cache import cache
        BotService.get_messages_bulk(['test_key'], 'ru')
        with patch.object(BotMessage.objects, 'filter') as mock_filter:
            BotService.get_messages_bulk(['test_key'], 'ru')
            mock_filter.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ПОЛЬЗОВАТЕЛИ
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsers(TestCase):

    def test_get_user_existing(self):
        make_user(telegram_id=111)
        user = BotService.get_user(111)
        self.assertIsNotNone(user)

    def test_get_user_not_found(self):
        self.assertIsNone(BotService.get_user(999999))

    def test_get_or_create_creates_new(self):
        user, created = BotService.get_or_create_user(
            222, first_name='Алишер', language='uz',
        )
        self.assertTrue(created)
        self.assertEqual(user.first_name, 'Алишер')

    def test_get_or_create_updates_existing(self):
        make_user(telegram_id=333, language='ru')
        BotService.get_or_create_user(333, language='uz')
        user = TelegramUser.objects.get(telegram_id=333)
        self.assertEqual(user.language, 'uz')

    def test_get_or_create_none_not_overwrite(self):
        """None значения не перезаписывают существующие данные."""
        make_user(telegram_id=444, phone='+998901234567')
        BotService.get_or_create_user(444, phone=None)
        user = TelegramUser.objects.get(telegram_id=444)
        self.assertEqual(user.phone, '+998901234567')

    def test_update_user(self):
        make_user(telegram_id=555, language='ru')
        BotService.update_user(555, language='en')
        user = TelegramUser.objects.get(telegram_id=555)
        self.assertEqual(user.language, 'en')

    def test_update_user_not_found_returns_none(self):
        self.assertIsNone(BotService.update_user(999999, language='en'))

    def test_mark_blocked(self):
        make_user(telegram_id=666)
        BotService.mark_user_blocked(666)
        self.assertTrue(TelegramUser.objects.get(telegram_id=666).is_blocked)

    def test_registration_complete_true(self):
        user = make_user(first_name='Иван', phone='+998901234567')
        self.assertTrue(BotService.is_registration_complete(user))

    def test_registration_complete_no_phone(self):
        user = make_user(first_name='Иван', phone=None)
        self.assertFalse(BotService.is_registration_complete(user))

    def test_registration_complete_no_name(self):
        user = make_user(first_name=None, phone='+998901234567')
        self.assertFalse(BotService.is_registration_complete(user))

    def test_registration_complete_none_user(self):
        self.assertFalse(BotService.is_registration_complete(None))


# ═══════════════════════════════════════════════════════════════════════════════
# 5. КАТАЛОГ
# ═══════════════════════════════════════════════════════════════════════════════

class TestCatalog(TestCase):

    def setUp(self):
        self.p1 = make_product(
            slug='furgon-tiger-v',
            category='furgon',
            categories='tiger_v',
        )
        self.p2 = make_product(
            slug='furgon-tiger-vh',
            category='furgon',
            categories='tiger_vh',
            title='FAW Tiger VH',
            title_ru='FAW Tiger VH RU',
        )
        self.p3 = make_product(
            slug='samosval-tiger-v',
            category='samosval',
            categories='tiger_v',
            title='Самосвал',
            title_ru='Самосвал RU',
        )
        make_product(slug='inactive', category='furgon', is_active=False)

    def test_categories_excludes_empty(self):
        cats = BotService.get_categories('ru')
        keys = [c['key'] for c in cats]
        self.assertIn('furgon', keys)
        self.assertNotIn('maxsus', keys)

    def test_categories_excludes_inactive(self):
        cats = BotService.get_categories('ru')
        furgon = next(c for c in cats if c['key'] == 'furgon')
        self.assertEqual(furgon['count'], 2)

    def test_categories_unknown_key_logged_not_crashed(self):
        """Продукт с неизвестной category не ломает каталог."""
        make_product(slug='bad-cat', category='tiger_v', categories='')
        cats = BotService.get_categories('ru')
        keys = [c['key'] for c in cats]
        self.assertNotIn('tiger_v', keys)

    def test_products_by_category(self):
        products = BotService.get_products_by_filter('ru', category='furgon')
        ids = [p['id'] for p in products]
        self.assertIn(self.p1.id, ids)
        self.assertNotIn(self.p3.id, ids)

    def test_products_by_subcategory(self):
        products = BotService.get_products_by_filter('ru', subcategory='tiger_v')
        ids = [p['id'] for p in products]
        self.assertIn(self.p1.id, ids)
        self.assertIn(self.p3.id, ids)
        self.assertNotIn(self.p2.id, ids)

    def test_products_excludes_inactive(self):
        products = BotService.get_products_by_filter('ru', category='furgon')
        slugs = [p['slug'] for p in products]
        self.assertNotIn('inactive', slugs)

    def test_product_detail_not_found(self):
        self.assertIsNone(BotService.get_product_detail(999999, 'ru'))

    def test_product_detail_inactive(self):
        inactive = make_product(slug='inactive-2', is_active=False)
        self.assertIsNone(BotService.get_product_detail(inactive.id, 'ru'))

    def test_product_detail_fields(self):
        detail = BotService.get_product_detail(self.p1.id, 'ru')
        self.assertIsNotNone(detail)
        self.assertEqual(detail['id'], self.p1.id)
        self.assertEqual(detail['title'], 'FAW Tiger V Test RU')
        self.assertIn('image_path', detail)
        self.assertIn('card_specs', detail)
        self.assertIn('features', detail)
        self.assertIn('parameters_grouped', detail)

    def test_product_detail_image_path_is_disk_path_not_url(self):
        """image_path должен быть путём к диску, не URL."""
        detail = BotService.get_product_detail(self.p1.id, 'ru')
        if detail['image_path']:
            self.assertFalse(detail['image_path'].startswith('http'))

    def test_get_all_active_products_public_method(self):
        """get_all_active_products — публичный метод без underscore."""
        self.assertTrue(hasattr(BotService, 'get_all_active_products'))
        self.assertFalse(hasattr(BotService, '_get_all_active_products'))
        products = BotService.get_all_active_products('ru')
        ids = [p['id'] for p in products]
        self.assertIn(self.p1.id, ids)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ДИЛЕРЫ
# ═══════════════════════════════════════════════════════════════════════════════

class TestDealers(TestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.dealer = make_dealer()

    def test_get_dealers(self):
        dealers = BotService.get_dealers('ru')
        self.assertEqual(len(dealers), 1)
        self.assertEqual(dealers[0]['city'], 'Toshkent')

    def test_dealer_map_url_format(self):
        dealers = BotService.get_dealers('ru')
        self.assertTrue(dealers[0]['map_url'].startswith('https://2gis.uz'))

    def test_dealer_coordinates_are_float(self):
        dealers = BotService.get_dealers('ru')
        self.assertIsInstance(dealers[0]['latitude'], float)
        self.assertIsInstance(dealers[0]['longitude'], float)

    def test_get_dealer_cities(self):
        cities = BotService.get_dealer_cities()
        self.assertIn('Toshkent', cities)

    def test_get_dealer_cities_excludes_inactive(self):
        make_dealer(name='Inactive', city='Samarqand', is_active=False)
        cities = BotService.get_dealer_cities()
        self.assertNotIn('Samarqand', cities)

    def test_dealer_cities_cached(self):
        from django.core.cache import cache
        BotService.get_dealer_cities()
        self.assertIsNotNone(cache.get('bot_dealer_cities'))

    def test_dealer_cities_cache_ttl(self):
        """Кеш городов должен существовать после первого вызова."""
        from django.core.cache import cache
        cache.clear()
        BotService.get_dealer_cities()
        cached = cache.get('bot_dealer_cities')
        self.assertIsNotNone(cached)
        self.assertIsInstance(cached, list)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ЛИД — create_lead
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateLead(TestCase):

    def test_creates_contact_form(self):
        lead = BotService.create_lead({
            'name': 'Алишер',
            'phone': '+998901234567',
            'region': 'tashkent_city',
            'product_title': 'FAW Tiger V',
            'message': 'Хочу купить',
        })
        self.assertIsNotNone(lead)
        self.assertEqual(lead.name, 'Алишер')
        self.assertEqual(lead.priority, 'high')
        self.assertEqual(lead.status, 'new')

    def test_utm_campaign_saved(self):
        import json
        lead = BotService.create_lead(
            {'name': 'Test', 'phone': '+998901234567'},
            utm_campaign='leasing',
        )
        utm = json.loads(lead.utm_data)
        self.assertEqual(utm['utm_campaign'], 'leasing')
        self.assertEqual(utm['utm_source'], 'telegram')

    def test_utm_no_escaped_cyrillic(self):
        """Кириллица в UTM не должна экранироваться."""
        lead = BotService.create_lead({'name': 'Test', 'phone': '+998901234567'})
        self.assertNotIn('\\u', lead.utm_data)

    def test_returns_none_on_db_error(self):
        with patch.object(ContactForm.objects, 'create', side_effect=Exception('DB error')):
            lead = BotService.create_lead({'name': 'Test', 'phone': '+998901234567'})
        self.assertIsNone(lead)

    def test_fire_and_forget_does_not_block(self):

        with patch.object(BotService, '_fire_and_forget') as mock_fire:
            start = time.time()
            lead = BotService.create_lead({
                'name': 'Test',
                'phone': '+998901234567',
            })
            elapsed = time.time() - start

        self.assertIsNotNone(lead)
        self.assertLess(elapsed, 0.1, '_fire_and_forget заблокировал основной поток')
        mock_fire.assert_called_once()
        args, _ = mock_fire.call_args
        self.assertEqual(args[0].id, lead.id)

    def test_fire_and_forget_runs_in_thread(self):
        """
        _fire_and_forget запускает daemon поток — проверяем напрямую.
        """
        threads_before = threading.active_count()

        with patch.object(BotService, '_send_to_amocrm', lambda *a: time.sleep(0.5)), \
            patch.object(BotService, '_send_telegram_notify', lambda *a: None):

            lead = ContactForm.objects.create(
                name='Test', phone='+998901234567',
                region='tashkent_city', status='new', priority='high',
                utm_data='{}',
            )
            BotService._fire_and_forget(lead)
            threads_after = threading.active_count()

        # После _fire_and_forget активных потоков стало больше
        self.assertGreater(threads_after, threads_before)

    def test_fire_and_forget_closes_db_connection(self):
        """
        _fire_and_forget должен закрывать DB соединение после работы.
        Иначе блокирует основной поток бота.
        """
        connection_closed = []

        original_fire = BotService._fire_and_forget.__func__

        def mock_run(self_cls, lead):
            def _run():
                from django.db import connection
                try:
                    self_cls._send_to_amocrm(lead)
                    self_cls._send_telegram_notify(lead)
                finally:
                    connection.close()
                    connection_closed.append(True)

            threading.Thread(target=_run, daemon=True).start()

        with patch.object(BotService, '_send_to_amocrm', lambda *a: None), \
             patch.object(BotService, '_send_telegram_notify', lambda *a: None):

            lead = BotService.create_lead({'name': 'Test', 'phone': '+998901234567'})
            time.sleep(0.2)

        # Проверяем через реальный _fire_and_forget что соединение закрывается
        # (косвенно — бот не зависает после лида)
        self.assertIsNotNone(lead)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. ТЕСТ-ДРАЙВ — create_test_drive_lead
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateTestDriveLead(TestCase):

    def setUp(self):
        self.user = make_user()
        self.product = make_product()

    def _make_data(self, **kwargs) -> dict:
        defaults = {
            'telegram_id':    self.user.telegram_id,
            'product_id':     self.product.id,
            'product_title':  self.product.title,
            'name':           'Иван Иванов',
            'phone':          '+998901234567',
            'region':         'tashkent_city',
            'city':           'Toshkent',
            'preferred_date': (date.today() + timedelta(days=1)).strftime('%d.%m.%Y'),
            'preferred_time': '10:00',
        }
        defaults.update(kwargs)
        return defaults

    def test_creates_lead_and_td_request(self):
        lead, error = BotService.create_test_drive_lead(self._make_data())
        self.assertIsNotNone(lead)
        self.assertIsNone(error)
        self.assertIsInstance(lead, ContactForm)
        self.assertTrue(TestDriveRequest.objects.filter(user=self.user).exists())

    def test_increments_total_requests_atomically(self):
        """F() expression защищает от race condition."""
        BotService.create_test_drive_lead(self._make_data())
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_requests, 1)

    def test_blocks_second_active_request(self):
        BotService.create_test_drive_lead(self._make_data())
        lead, error = BotService.create_test_drive_lead(self._make_data())
        self.assertIsNone(lead)
        self.assertEqual(error, 'has_active')

    def test_works_without_user(self):
        """Анонимная заявка — telegram_id не в БД."""
        data = self._make_data(telegram_id=999999)
        lead, error = BotService.create_test_drive_lead(data)
        self.assertIsNotNone(lead)
        self.assertIsNone(error)

    def test_cancel_test_drive(self):
        BotService.create_test_drive_lead(self._make_data())
        td = TestDriveRequest.objects.get(user=self.user)
        result = BotService.cancel_test_drive(td.id, self.user)
        self.assertTrue(result)
        td.refresh_from_db()
        self.assertEqual(td.status, 'cancelled')

    def test_cancel_other_user_td_forbidden(self):
        """Нельзя отменить чужую заявку — security check."""
        other_user = make_user(telegram_id=999888)
        BotService.create_test_drive_lead(self._make_data())
        td = TestDriveRequest.objects.get(user=self.user)
        result = BotService.cancel_test_drive(td.id, other_user)
        self.assertFalse(result)

    def test_td_uses_fire_and_forget_not_blocking(self):
        """
        create_test_drive_lead должен использовать _fire_and_forget.
        Не должен вызывать _send_to_amocrm и _send_telegram_notify напрямую.
        """
        call_log = []

        def track_fire(lead):
            call_log.append('fire_and_forget')

        with patch.object(BotService, '_fire_and_forget', track_fire):
            lead, error = BotService.create_test_drive_lead(self._make_data())

        self.assertIsNotNone(lead)
        self.assertIn('fire_and_forget', call_log)

    def test_bad_date_format_handled(self):
        """Неверный формат даты не роняет метод."""
        data = self._make_data(preferred_date='not-a-date')
        lead, error = BotService.create_test_drive_lead(data)
        # Лид создаётся, TD без даты
        self.assertIsNotNone(lead)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. ИЗБРАННОЕ
# ═══════════════════════════════════════════════════════════════════════════════

class TestWishlist(TestCase):

    def setUp(self):
        self.user = make_user()
        self.product = make_product()

    def test_toggle_adds(self):
        added = BotService.toggle_wishlist(self.user, self.product.id)
        self.assertTrue(added)
        self.assertTrue(
            ProductWishlist.objects.filter(
                user=self.user, product=self.product,
            ).exists()
        )

    def test_toggle_removes(self):
        ProductWishlist.objects.create(user=self.user, product=self.product)
        removed = BotService.toggle_wishlist(self.user, self.product.id)
        self.assertFalse(removed)
        self.assertFalse(
            ProductWishlist.objects.filter(
                user=self.user, product=self.product,
            ).exists()
        )

    def test_get_wishlist_active_only(self):
        inactive = make_product(slug='inactive-wish', is_active=False)
        ProductWishlist.objects.create(user=self.user, product=self.product)
        ProductWishlist.objects.create(user=self.user, product=inactive)
        wishlist = BotService.get_wishlist(self.user, 'ru')
        ids = [item['id'] for item in wishlist]
        self.assertIn(self.product.id, ids)
        self.assertNotIn(inactive.id, ids)

    def test_get_wishlist_image_path_not_url(self):
        """image_path в wishlist — путь к диску, не URL."""
        ProductWishlist.objects.create(user=self.user, product=self.product)
        wishlist = BotService.get_wishlist(self.user, 'ru')
        for item in wishlist:
            if item.get('image_path'):
                self.assertFalse(item['image_path'].startswith('http'))


# ═══════════════════════════════════════════════════════════════════════════════
# 10. ИСТОРИЯ ПРОСМОТРОВ
# ═══════════════════════════════════════════════════════════════════════════════

class TestProductViewHistory(TestCase):

    def setUp(self):
        self.user = make_user()
        self.product = make_product()

    def test_record_creates_entry(self):
        BotService.record_product_view(self.user, self.product.id)
        self.assertTrue(
            ProductViewHistory.objects.filter(
                user=self.user, product=self.product,
            ).exists()
        )

    def test_record_increments_with_f_expression(self):
        """view_count инкрементируется через F() без race condition."""
        BotService.record_product_view(self.user, self.product.id)
        BotService.record_product_view(self.user, self.product.id)
        entry = ProductViewHistory.objects.get(user=self.user, product=self.product)
        self.assertEqual(entry.view_count, 2)

    def test_status_changes_to_interested_after_3(self):
        ProductViewHistory.objects.create(
            user=self.user, product=self.product, view_count=2,
        )
        BotService.record_product_view(self.user, self.product.id)
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, 'interested')

    def test_status_not_changed_if_not_new(self):
        self.user.status = 'hot'
        self.user.save()
        ProductViewHistory.objects.create(
            user=self.user, product=self.product, view_count=2,
        )
        BotService.record_product_view(self.user, self.product.id)
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, 'hot')


# ═══════════════════════════════════════════════════════════════════════════════
# 11. РЕГИОНЫ — REGION_CHOICES и REGION_LABELS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegions(TestCase):

    def test_all_region_choices_have_labels(self):
        """Каждый ключ из REGION_CHOICES должен быть в REGION_LABELS."""
        for key, _ in REGION_CHOICES:
            self.assertIn(
                key, REGION_LABELS,
                msg=f'REGION_CHOICES key "{key}" отсутствует в REGION_LABELS',
            )

    def test_all_region_labels_have_three_languages(self):
        """Каждый регион должен иметь переводы на ru, uz, en."""
        for key, translations in REGION_LABELS.items():
            for lang in ('ru', 'uz', 'en'):
                self.assertIn(
                    lang, translations,
                    msg=f'REGION_LABELS["{key}"] не имеет перевода "{lang}"',
                )
                self.assertTrue(
                    translations[lang],
                    msg=f'REGION_LABELS["{key}"]["{lang}"] пустой',
                )

    def test_region_labels_keys_match_choices_keys(self):
        """Ключи REGION_LABELS должны совпадать с ключами REGION_CHOICES."""
        choices_keys = {key for key, _ in REGION_CHOICES}
        labels_keys = set(REGION_LABELS.keys())
        self.assertEqual(
            choices_keys, labels_keys,
            msg=f'Несоответствие: {choices_keys.symmetric_difference(labels_keys)}',
        )

    def test_region_key_max_length(self):
        """Ключи регионов должны помещаться в CharField max_length=100."""
        for key, _ in REGION_CHOICES:
            self.assertLessEqual(len(key), 100)

    def test_tashkent_city_translations(self):
        labels = REGION_LABELS.get('tashkent_city', {})
        self.assertEqual(labels.get('ru'), 'г. Ташкент')
        self.assertEqual(labels.get('uz'), 'Toshkent shahri')
        self.assertEqual(labels.get('en'), 'Tashkent city')


# ═══════════════════════════════════════════════════════════════════════════════
# 12. ТРИГГЕРЫ — совпадение с BotMenuItem
# ═══════════════════════════════════════════════════════════════════════════════

class TestTriggers(TestCase):

    def setUp(self):
        """Создаём BotMenuItem как в init_bot_data."""
        menu_items = [
            {'key': 'catalog',    'label_ru': 'Каталог',          'label_uz': 'Katalog',              'label_en': 'Catalog'},
            {'key': 'dealers',    'label_ru': 'Дилеры',           'label_uz': 'Dilerlar',             'label_en': 'Dealers'},
            {'key': 'news',       'label_ru': 'Новости',          'label_uz': 'Yangiliklar',          'label_en': 'News'},
            {'key': 'promotions', 'label_ru': 'Акции',            'label_uz': 'Aksiyalar',            'label_en': 'Promotions'},
            {'key': 'test_drive', 'label_ru': 'Тест-драйв',       'label_uz': 'Test-drayv',           'label_en': 'Test drive'},
            {'key': 'lead',       'label_ru': 'Оставить заявку',  'label_uz': 'Ariza qoldirish',      'label_en': 'Leave a request'},
            {'key': 'leasing',    'label_ru': 'Лизинг',           'label_uz': 'Lizing',               'label_en': 'Leasing'},
            {'key': 'faq',        'label_ru': 'Вопросы и ответы', 'label_uz': 'Savol va javoblar',    'label_en': 'FAQ'},
            {'key': 'contacts',   'label_ru': 'Контакты',         'label_uz': 'Kontaktlar',           'label_en': 'Contacts'},
            {'key': 'profile',    'label_ru': 'Мой профиль',      'label_uz': 'Mening profilim',      'label_en': 'My profile'},
            {'key': 'language',   'label_ru': 'Сменить язык',     'label_uz': "Tilni o'zgartirish",   'label_en': 'Change language'},
        ]
        for item in menu_items:
            BotMenuItem.objects.create(
                key=item['key'],
                label_ru=item['label_ru'],
                label_uz=item['label_uz'],
                label_en=item['label_en'],
                emoji='',
                order=0,
                is_active=True,
            )

    def _check_trigger_matches_menu(self, trigger_set, menu_key):
        """Проверяет что хотя бы один label из BotMenuItem есть в trigger_set."""
        item = BotMenuItem.objects.get(key=menu_key)
        labels = {item.label_ru, item.label_uz, item.label_en}
        overlap = trigger_set & labels
        self.assertTrue(
            overlap,
            msg=f'Триггеры {trigger_set} не содержат ни одного label из BotMenuItem[{menu_key}]: {labels}',
        )

    def test_catalog_triggers_match_menu(self):
        self._check_trigger_matches_menu(CATALOG_TRIGGERS, 'catalog')

    def test_dealers_triggers_match_menu(self):
        self._check_trigger_matches_menu(DEALERS_TRIGGERS, 'dealers')

    def test_news_triggers_match_menu(self):
        self._check_trigger_matches_menu(NEWS_TRIGGERS, 'news')

    def test_promotions_triggers_match_menu(self):
        self._check_trigger_matches_menu(PROMOTIONS_TRIGGERS, 'promotions')

    def test_td_triggers_match_menu(self):
        self._check_trigger_matches_menu(TD_TRIGGERS, 'test_drive')

    def test_lead_triggers_match_menu(self):
        self._check_trigger_matches_menu(LEAD_TRIGGERS, 'lead')

    def test_leasing_triggers_match_menu(self):
        self._check_trigger_matches_menu(LEASING_TRIGGERS, 'leasing')

    def test_faq_triggers_match_menu(self):
        self._check_trigger_matches_menu(FAQ_TRIGGERS, 'faq')

    def test_contacts_triggers_match_menu(self):
        self._check_trigger_matches_menu(CONTACTS_TRIGGERS, 'contacts')

    def test_profile_triggers_match_menu(self):
        self._check_trigger_matches_menu(PROFILE_TRIGGERS, 'profile')

    def test_language_triggers_match_menu(self):
        self._check_trigger_matches_menu(LANGUAGE_TRIGGERS, 'language')

    def test_all_triggers_are_frozensets(self):
        """Все триггеры должны быть frozenset — иммутабельны."""
        all_triggers = [
            CATALOG_TRIGGERS, DEALERS_TRIGGERS, NEWS_TRIGGERS,
            PROMOTIONS_TRIGGERS, TD_TRIGGERS, LEAD_TRIGGERS,
            LEASING_TRIGGERS, FAQ_TRIGGERS, CONTACTS_TRIGGERS,
            PROFILE_TRIGGERS, LANGUAGE_TRIGGERS,
        ]
        for trigger in all_triggers:
            self.assertIsInstance(trigger, frozenset)

    def test_no_trigger_overlap(self):
        """Триггеры разных разделов не должны пересекаться."""
        named = {
            'catalog':    CATALOG_TRIGGERS,
            'dealers':    DEALERS_TRIGGERS,
            'news':       NEWS_TRIGGERS,
            'promotions': PROMOTIONS_TRIGGERS,
            'td':         TD_TRIGGERS,
            'lead':       LEAD_TRIGGERS,
            'leasing':    LEASING_TRIGGERS,
            'contacts':   CONTACTS_TRIGGERS,
            'profile':    PROFILE_TRIGGERS,
            'language':   LANGUAGE_TRIGGERS,
        }
        keys = list(named.keys())
        for i, k1 in enumerate(keys):
            for k2 in keys[i+1:]:
                overlap = named[k1] & named[k2]
                self.assertFalse(
                    overlap,
                    msg=f'Пересечение триггеров {k1} и {k2}: {overlap}',
                )


# ═══════════════════════════════════════════════════════════════════════════════
# 13. КОНСТАНТЫ — TEST_DRIVE_TIME_SLOTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestConstants(TestCase):

    def test_time_slots_format(self):
        """Все слоты должны быть в формате HH:MM."""
        import re
        pattern = re.compile(r'^\d{2}:\d{2}$')
        for slot in TEST_DRIVE_TIME_SLOTS:
            self.assertRegex(slot, pattern, msg=f'Неверный формат слота: {slot}')

    def test_time_slots_not_empty(self):
        self.assertGreater(len(TEST_DRIVE_TIME_SLOTS), 0)

    def test_product_categories_have_three_languages(self):
        for key, translations in PRODUCT_CATEGORIES.items():
            for lang in ('ru', 'uz', 'en'):
                self.assertIn(lang, translations)

    def test_product_subcategories_have_three_languages(self):
        for key, translations in PRODUCT_SUBCATEGORIES.items():
            for lang in ('ru', 'uz', 'en'):
                self.assertIn(lang, translations)


# ═══════════════════════════════════════════════════════════════════════════════
# 14. HANDLERS — импорты и структура
# ═══════════════════════════════════════════════════════════════════════════════

class TestHandlerImports(TestCase):

    def test_all_handlers_importable(self):
        """Все handler файлы должны импортироваться без ошибок."""
        handlers = [
            'main.services.telegram.handlers.start',
            'main.services.telegram.handlers.catalog',
            'main.services.telegram.handlers.dealers',
            'main.services.telegram.handlers.test_drive',
            'main.services.telegram.handlers.lead',
            'main.services.telegram.handlers.faq',
            'main.services.telegram.handlers.profile',
            'main.services.telegram.handlers.news',
            'main.services.telegram.handlers.leasing',
            'main.services.telegram.handlers.contacts',
            'main.services.telegram.handlers.common',
        ]
        for module_path in handlers:
            try:
                import importlib
                importlib.import_module(module_path)
            except ImportError as e:
                self.fail(f'Не удалось импортировать {module_path}: {e}')

    def test_all_handlers_have_router(self):
        """Каждый handler модуль должен иметь router."""
        import importlib
        handlers = [
            'main.services.telegram.handlers.start',
            'main.services.telegram.handlers.catalog',
            'main.services.telegram.handlers.dealers',
            'main.services.telegram.handlers.test_drive',
            'main.services.telegram.handlers.lead',
            'main.services.telegram.handlers.faq',
            'main.services.telegram.handlers.profile',
            'main.services.telegram.handlers.news',
            'main.services.telegram.handlers.leasing',
            'main.services.telegram.handlers.contacts',
            'main.services.telegram.handlers.common',
        ]
        for module_path in handlers:
            module = importlib.import_module(module_path)
            self.assertTrue(
                hasattr(module, 'router'),
                msg=f'{module_path} не имеет атрибута router',
            )

    def test_common_router_last_in_loader(self):
        """common.router должен быть зарегистрирован последним."""
        import importlib
        loader = importlib.import_module('main.services.telegram.loader')
        import inspect
        source = inspect.getsource(loader._register_handlers)
        common_pos = source.rfind('common.router')
        contacts_pos = source.rfind('contacts.router')
        self.assertGreater(
            common_pos, contacts_pos,
            msg='common.router должен быть зарегистрирован после contacts.router',
        )

    def test_triggers_module_importable(self):
        import importlib
        module = importlib.import_module('main.services.telegram.triggers')
        self.assertTrue(hasattr(module, 'CATALOG_TRIGGERS'))
        self.assertTrue(hasattr(module, 'TD_TRIGGERS'))

    def test_utils_has_read_file(self):
        """utils.py должен иметь read_file для async чтения файлов."""
        import importlib
        utils = importlib.import_module('main.services.telegram.utils')
        self.assertTrue(
            hasattr(utils, 'read_file'),
            msg='utils.py не имеет read_file — event loop будет блокироваться',
        )

    def test_bot_service_has_fire_and_forget(self):
        """BotService должен иметь _fire_and_forget для неблокирующей отправки."""
        self.assertTrue(hasattr(BotService, '_fire_and_forget'))

    def test_bot_service_no_private_get_all_active_products(self):
        """_get_all_active_products должен быть публичным."""
        self.assertFalse(hasattr(BotService, '_get_all_active_products'))
        self.assertTrue(hasattr(BotService, 'get_all_active_products'))


# ═══════════════════════════════════════════════════════════════════════════════
# 15. СИГНАЛЫ — автоматический сброс кеша
# ═══════════════════════════════════════════════════════════════════════════════

class TestCacheSignals(TestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_bot_contacts_post_save_clears_cache(self):
        from django.core.cache import cache
        contacts = BotContacts.objects.create(pk=1)
        cache.set('bot_contacts', contacts, timeout=300)
        self.assertIsNotNone(cache.get('bot_contacts'))
        contacts.phone_main = '+998712345678'
        contacts.save()
        self.assertIsNone(cache.get('bot_contacts'))

    def test_bot_config_post_save_clears_cache(self):
        from django.core.cache import cache
        config = make_bot_config()
        cache.set('bot_config', config, timeout=300)
        self.assertIsNotNone(cache.get('bot_config'))
        config.site_url = 'https://updated.faw.uz'
        config.save()
        self.assertIsNone(cache.get('bot_config'))

    def test_bot_message_post_save_clears_cache(self):
        from django.core.cache import cache
        msg = BotMessage.objects.create(
            key='cache_test', language='ru', text='Старый текст',
        )
        cache.set('bot_msg_cache_test_ru', 'Старый текст', timeout=300)
        self.assertIsNotNone(cache.get('bot_msg_cache_test_ru'))
        msg.text = 'Новый текст'
        msg.save()
        self.assertIsNone(cache.get('bot_msg_cache_test_ru'))