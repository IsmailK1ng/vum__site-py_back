import json
import logging
import threading

from datetime import datetime, timedelta
from typing import Optional

from django.core.cache import cache
from django.db import transaction
from django.db.models import F, Count, Q
from django.utils import timezone

from main.models import (
    BotBroadcast,
    BotConfig,
    BotContacts,
    BotMessage,
    BotMenuItem,
    ContactForm,
    Dealer,
    FAQItem,
    News,
    Product,
    ProductParameter,
    ProductViewHistory,
    ProductWishlist,
    Promotion,
    TelegramUser,
    TestDriveRequest,
)

logger = logging.getLogger('bot')

# ─── Константы ───────────────────────────────────────────────────────────────

_CONFIG_CACHE_TTL  = 60
_MSG_CACHE_TTL     = 300
_CITIES_CACHE_TTL  = 300

TEST_DRIVE_TIME_SLOTS = [
    '09:00', '10:00', '11:00', '12:00',
    '14:00', '15:00', '16:00', '17:00',
]


PRODUCT_CATEGORIES = {
    'samosval': {'ru': 'Самосвалы',   'uz': 'Самосваллар',    'en': 'Dump Trucks'},
    'maxsus':   {'ru': 'Спецтехника', 'uz': 'Maxsus texnika', 'en': 'Special Equipment'},
    'furgon':   {'ru': 'Фургоны',     'uz': 'Avtofurgonlar',  'en': 'Vans'},
    'shassi':   {'ru': 'Шасси',       'uz': 'Shassilar',      'en': 'Chassis'},
}

PRODUCT_SUBCATEGORIES = {
    'tiger_v':  {'ru': 'Tiger V',  'uz': 'Tiger V',  'en': 'Tiger V'},
    'tiger_vh': {'ru': 'Tiger VH', 'uz': 'Tiger VH', 'en': 'Tiger VH'},
    'tiger_vr': {'ru': 'Tiger VR', 'uz': 'Tiger VR', 'en': 'Tiger VR'},
}

PARAM_CATEGORY_LABELS = {
    'main':           {'ru': 'Основные параметры', 'uz': 'Asosiy parametrlar',  'en': 'Main parameters'},
    'engine':         {'ru': 'Двигатель',           'uz': 'Dvigatel',            'en': 'Engine'},
    'weight':         {'ru': 'Весовые параметры',   'uz': 'Vazn parametrlari',   'en': 'Weight'},
    'transmission':   {'ru': 'Трансмиссия',         'uz': 'Transmissiya',        'en': 'Transmission'},
    'brakes':         {'ru': 'Тормоза и шины',      'uz': 'Tormoz va shinalar',  'en': 'Brakes & Tires'},
    'comfort':        {'ru': 'Комфорт',             'uz': 'Qulaylik',            'en': 'Comfort'},
    'superstructure': {'ru': 'Надстройка',          'uz': 'Ustqurulma',          'en': 'Superstructure'},
    'cabin':          {'ru': 'Кабина',              'uz': 'Kabina',              'en': 'Cabin'},
    'additional':     {'ru': 'Дополнительно',       'uz': "Qo'shimcha",          'en': 'Additional'},
}


# ─── Вспомогательные функции ─────────────────────────────────────────────────

def _t(translations: dict, language: str) -> str:
    return translations.get(language) or translations.get('ru', '')


def _field(obj, field_name: str, language: str) -> str:
    return (
        getattr(obj, f'{field_name}_{language}', None)
        or getattr(obj, field_name, None)
        or ''
    )


def _image_path(img_field) -> Optional[str]:
    if not img_field:
        return None
    from django.conf import settings
    full_path = settings.MEDIA_ROOT / img_field.name
    return str(full_path) if full_path.exists() else None


def _q_promotion_active() -> Q:
    now = timezone.now()
    return (
        Q(is_active=True)
        & Q(start_date__lte=now)
        & (Q(end_date__isnull=True) | Q(end_date__gte=now))
    )


def _q_broadcast_ready(now) -> Q:
    return (
        Q(status='scheduled')
        & (Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=now))
    )


def _build_utm(campaign: str) -> str:
    return json.dumps(
        {
            'utm_source':   'telegram',
            'utm_medium':   'bot',
            'utm_campaign': campaign,
        },
        ensure_ascii=False,
    )


# ─── Сервисный класс ─────────────────────────────────────────────────────────

class BotService:

    @classmethod
    def get_config(cls) -> BotConfig:
        cached = cache.get('bot_config')
        if cached is not None:
            return cached
        config = BotConfig.get_instance()
        cache.set('bot_config', config, timeout=_CONFIG_CACHE_TTL)
        return config

    @classmethod
    def invalidate_config_cache(cls) -> None:
        cache.delete('bot_config')

    @classmethod
    def _fire_and_forget(cls, lead: ContactForm) -> None:
        def _run():
            try:
                cls._send_to_amocrm(lead)
                cls._send_telegram_notify(lead)
            finally:
                from django.db import connection
                connection.close()

        threading.Thread(target=_run, daemon=True).start()

    # =========================================================================
    # ТЕКСТЫ
    # =========================================================================

    @classmethod
    def get_message(cls, key: str, language: str, **kwargs) -> str:
        cache_key = f'bot_msg_{key}_{language}'
        text = cache.get(cache_key)

        if text is None:
            obj = (
                BotMessage.objects
                .filter(key=key, language=language)
                .only('text')
                .first()
            )
            if obj is None and language != 'ru':
                obj = (
                    BotMessage.objects
                    .filter(key=key, language='ru')
                    .only('text')
                    .first()
                )
            text = obj.text if obj else key
            cache.set(cache_key, text, timeout=_MSG_CACHE_TTL)

        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError) as exc:
                logger.warning(
                    'BotMessage format error key=%s lang=%s: %s',
                    key, language, exc,
                )

        return text

    @classmethod
    def get_messages_bulk(cls, keys: list[str], language: str) -> dict[str, str]:
        result = {}
        missing_keys = []

        for key in keys:
            cache_key = f'bot_msg_{key}_{language}'
            cached = cache.get(cache_key)
            if cached is not None:
                result[key] = cached
            else:
                missing_keys.append(key)

        if missing_keys:
            qs = BotMessage.objects.filter(
                key__in=missing_keys,
                language=language,
            ).only('key', 'text')
            found = {obj.key: obj.text for obj in qs}

            if language != 'ru':
                still_missing = [k for k in missing_keys if k not in found]
                if still_missing:
                    ru_qs = BotMessage.objects.filter(
                        key__in=still_missing,
                        language='ru',
                    ).only('key', 'text')
                    for obj in ru_qs:
                        if obj.key not in found:
                            found[obj.key] = obj.text

            for key in missing_keys:
                text = found.get(key, key) 
                cache.set(f'bot_msg_{key}_{language}', text, timeout=_MSG_CACHE_TTL)
                result[key] = text

        return result

    @classmethod
    def invalidate_message_cache(cls, key: str, language: str) -> None:
        cache.delete(f'bot_msg_{key}_{language}')

    # =========================================================================
    # МЕНЮ
    # =========================================================================

    @classmethod
    def get_menu_items(cls, language: str) -> list[dict]:
        cache_key = f'bot_menu_{language}'
        items = cache.get(cache_key)

        if items is None:
            qs = (
                BotMenuItem.objects
                .filter(is_active=True)
                .order_by('order')
                .only('key', 'label_ru', 'label_uz', 'label_en', 'emoji')
            )
            items = [
                {'key': item.key, 'label': item.get_label(language)}
                for item in qs
            ]
            cache.set(cache_key, items, timeout=_MSG_CACHE_TTL)

        return items

    # =========================================================================
    # ПОЛЬЗОВАТЕЛИ
    # =========================================================================

    @classmethod
    def get_user(cls, telegram_id: int) -> Optional[TelegramUser]:
        return TelegramUser.objects.filter(telegram_id=telegram_id).first()

    @classmethod
    def get_or_create_user(
        cls,
        telegram_id: int,
        **kwargs,
    ) -> tuple[TelegramUser, bool]:
        user, created = TelegramUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults=kwargs,
        )
        if not created and kwargs:
            fields_to_update = {k: v for k, v in kwargs.items() if v is not None}
            if fields_to_update:
                fields_to_update['last_active'] = timezone.now()
                TelegramUser.objects.filter(pk=user.pk).update(**fields_to_update)
                for k, v in fields_to_update.items():
                    setattr(user, k, v)
        return user, created

    @classmethod
    def update_user(cls, telegram_id: int, **kwargs) -> Optional[TelegramUser]:
        updated = TelegramUser.objects.filter(telegram_id=telegram_id).update(**kwargs)
        if updated:
            return TelegramUser.objects.get(telegram_id=telegram_id)
        return None

    @classmethod
    def mark_user_blocked(cls, telegram_id: int) -> None:
        TelegramUser.objects.filter(telegram_id=telegram_id).update(is_blocked=True)

    @classmethod
    def is_registration_complete(cls, user: Optional[TelegramUser]) -> bool:
        return bool(user and user.first_name and user.phone)

    # =========================================================================
    # КАТАЛОГ — категории
    # =========================================================================

    @classmethod
    def get_categories(cls, language: str) -> list[dict]:
        qs = (
            Product.objects
            .filter(is_active=True)
            .values('category')
            .annotate(count=Count('id'))
            .order_by('category')
        )
        result = []
        for row in qs:
            translations = PRODUCT_CATEGORIES.get(row['category'])
            if translations:
                result.append({
                    'key':   row['category'],
                    'label': _t(translations, language),
                    'count': row['count'],
                })
            else:
                logger.warning(
                    'get_categories: unknown category=%s, product excluded from catalog',
                    row['category'],
                )
        return result

    @classmethod
    def get_subcategories_for_category(
        cls,
        category: str,
        language: str,
    ) -> list[dict]:
        qs = (
            Product.objects
            .filter(is_active=True, category=category)
            .exclude(categories__isnull=True)
            .exclude(categories='')
            .values('categories')
            .annotate(count=Count('id'))
            .order_by('categories')
        )
        result = []
        for row in qs:
            translations = PRODUCT_SUBCATEGORIES.get(row['categories'])
            if translations:
                result.append({
                    'key':   row['categories'],
                    'label': _t(translations, language),
                    'count': row['count'],
                })
        return result

    @classmethod
    def get_subcategories_all(cls, language: str) -> list[dict]:
        qs = (
            Product.objects
            .filter(is_active=True)
            .exclude(categories__isnull=True)
            .exclude(categories='')
            .values('categories')
            .annotate(count=Count('id'))
            .order_by('categories')
        )
        result = []
        for row in qs:
            translations = PRODUCT_SUBCATEGORIES.get(row['categories'])
            if translations:
                result.append({
                    'key':   row['categories'],
                    'label': _t(translations, language),
                    'count': row['count'],
                })
        return result

    # =========================================================================
    # КАТАЛОГ — продукты
    # =========================================================================

    @classmethod
    def get_products_by_filter(
        cls,
        language: str,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> list[dict]:
        qs = Product.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)
        if subcategory:
            qs = qs.filter(categories=subcategory)
        qs = qs.order_by('order', 'title')

        return [
            {
                'id':            p.id,
                'title':         _field(p, 'title', language),
                'slug':          p.slug,
                'price':         _field(p, 'slider_price', language),
                'price_is_from': p.price_is_from,
            }
            for p in qs
        ]

    @classmethod
    def get_product_detail(cls, product_id: int, language: str) -> Optional[dict]:
        try:
            p = (
                Product.objects
                .prefetch_related('card_specs', 'features', 'parameters')
                .get(id=product_id, is_active=True)
            )
        except Product.DoesNotExist:
            logger.warning('get_product_detail: product not found id=%s', product_id)
            return None

        image_path = _image_path(p.card_image or p.main_image)

        card_specs = [
            v for spec in p.card_specs.all()
            if (v := _field(spec, 'value', language))
        ]
        features = [
            v for feat in p.features.all()
            if (v := _field(feat, 'name', language))
        ]

        parameters_grouped: dict[str, dict] = {}
        for param in p.parameters.all():
            cat = param.category
            if cat not in parameters_grouped:
                label = _t(
                    PARAM_CATEGORY_LABELS.get(cat, {'ru': cat, 'uz': cat, 'en': cat}),
                    language,
                )
                parameters_grouped[cat] = {'label': label, 'items': []}
            if text := _field(param, 'text', language):
                parameters_grouped[cat]['items'].append(text)

        return {
            'id':                 p.id,
            'title':              _field(p, 'title', language),
            'slug':               p.slug,
            'category':           p.category,
            'subcategory':        p.categories or '',
            'year':               p.slider_year or '',
            'price':              _field(p, 'slider_price', language),
            'price_is_from':      p.price_is_from,
            'power':              _field(p, 'slider_power', language),
            'fuel_consumption':   _field(p, 'slider_fuel_consumption', language),
            'image_path':         image_path,
            'card_specs':         card_specs,
            'features':           features,
            'parameters_grouped': parameters_grouped,
        }

    @classmethod
    def get_all_active_products(cls, language: str) -> list[dict]:
        return [
            {'id': p.id, 'title': _field(p, 'title', language)}
            for p in Product.objects.filter(is_active=True).order_by('order', 'title')
        ]

    @classmethod
    def get_product_title(cls, product_id: int, language: str) -> str:
        try:
            p = Product.objects.get(id=product_id, is_active=True)
            return _field(p, 'title', language)
        except Product.DoesNotExist:
            logger.warning('get_product_title: product id=%s not found', product_id)
            return ''

    # =========================================================================
    # КАТАЛОГ — продукты с ценами (для лизинга)
    # =========================================================================

    @classmethod
    def get_products_with_prices(
        cls,
        language: str,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> list[dict]:
        qs = (
            Product.objects
            .filter(is_active=True)
            .exclude(slider_price_ru__isnull=True)
            .exclude(slider_price_ru='')
            .prefetch_related('card_specs', 'features')
            .order_by('order', 'title')
        )
        if category:
            qs = qs.filter(category=category)
        if subcategory:
            qs = qs.filter(categories=subcategory)

        result = []
        for p in qs:
            price_str = _field(p, 'slider_price', language)
            price_num = int(''.join(filter(str.isdigit, price_str))) if price_str else 0
            if not price_num:
                continue

            card_specs = [
                v for spec in p.card_specs.all()
                if (v := _field(spec, 'value', language))
            ]
            features = [
                v for feat in p.features.all()
                if (v := _field(feat, 'name', language))
            ]

            result.append({
                'id':         p.id,
                'title':      _field(p, 'title', language),
                'slug':       p.slug,
                'price':      price_num,
                'price_str':  price_str,
                'year':       p.slider_year or '',
                'power':      _field(p, 'slider_power', language),
                'image_path': _image_path(p.card_image or p.main_image),
                'card_specs': card_specs,
                'features':   features,
            })
        return result

    @classmethod
    def get_categories_with_prices(cls, language: str) -> list[dict]:
        qs = (
            Product.objects
            .filter(is_active=True)
            .exclude(slider_price_ru__isnull=True)
            .exclude(slider_price_ru='')
            .values('category')
            .annotate(count=Count('id'))
            .order_by('category')
        )
        result = []
        for row in qs:
            translations = PRODUCT_CATEGORIES.get(row['category'])
            if translations:
                result.append({
                    'key':   row['category'],
                    'label': _t(translations, language),
                    'count': row['count'],
                })
        return result

    @classmethod
    def get_subcategories_with_prices(cls, language: str) -> list[dict]:
        qs = (
            Product.objects
            .filter(is_active=True)
            .exclude(slider_price_ru__isnull=True)
            .exclude(slider_price_ru='')
            .exclude(categories__isnull=True)
            .exclude(categories='')
            .values('categories')
            .annotate(count=Count('id'))
            .order_by('categories')
        )
        result = []
        for row in qs:
            translations = PRODUCT_SUBCATEGORIES.get(row['categories'])
            if translations:
                result.append({
                    'key':   row['categories'],
                    'label': _t(translations, language),
                    'count': row['count'],
                })
        return result

    # =========================================================================
    # ДИЛЕРЫ
    # =========================================================================

    @classmethod
    def _dealer_to_dict(cls, d: Dealer, language: str) -> dict:
        try:
            lat = float(d.latitude)
            lng = float(d.longitude)
        except (TypeError, ValueError):
            logger.warning('Dealer id=%s has invalid coordinates', d.id)
            lat, lng = 0.0, 0.0
        return {
            'id':            d.id,
            'name':          d.name,
            'city':          d.city,
            'address':       _field(d, 'address', language),
            'phone':         d.phone,
            'working_hours': _field(d, 'working_hours', language),
            'latitude':      lat,
            'longitude':     lng,
            'map_url':       f'https://2gis.uz/geo/{lng},{lat}',
        }

    @classmethod
    def get_dealers(cls, language: str) -> list[dict]:
        dealers = Dealer.objects.filter(is_active=True).order_by('order', 'city')
        return [cls._dealer_to_dict(d, language) for d in dealers]

    @classmethod
    def get_dealer_cities(cls) -> list[str]:
        cache_key = 'bot_dealer_cities'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        cities = list(
            Dealer.objects
            .filter(is_active=True)
            .values_list('city', flat=True)
            .distinct()
            .order_by('city')
        )
        cache.set(cache_key, cities, timeout=_CITIES_CACHE_TTL)
        return cities

    @classmethod
    def get_dealers_by_city(cls, city: str, language: str) -> list[dict]:
        dealers = (
            Dealer.objects
            .filter(is_active=True, city=city)
            .order_by('order', 'name')
        )
        return [cls._dealer_to_dict(d, language) for d in dealers]

    # =========================================================================
    # КОНТЕНТ
    # =========================================================================

    @classmethod
    def get_news(cls, language: str, limit: int = 5) -> list[dict]:
        limit = max(1, min(limit, 50))
        qs = (
            News.objects
            .filter(is_active=True)
            .order_by('-order', '-created_at', '-id')[:limit]
        )
        return [
            {
                'id':         n.id,
                'title':      _field(n, 'title', language),
                'desc':       _field(n, 'desc', language),
                'slug':       n.slug,
                'date':       n.created_at,
                'image_path': _image_path(n.preview_image),
            }
            for n in qs
        ]

    @classmethod
    def get_active_promotions(cls, language: str) -> list[dict]:
        qs = (
            Promotion.objects
            .filter(_q_promotion_active())
            .order_by('-priority', '-created_at')
        )
        return [
            {
                'id':          promo.id,
                'title':       _field(promo, 'title', language),
                'description': _field(promo, 'description', language),
                'button_text': _field(promo, 'button_text', language),
                'link':        promo.link,
                'end_date':    promo.end_date,
                'image_path':  _image_path(promo.image),
            }
            for promo in qs
        ]

    @classmethod
    def get_faq_items(cls, language: str) -> list[dict]:
        return [
            {
                'id':       item.id,
                'question': _field(item, 'question', language),
                'answer':   _field(item, 'answer', language),
            }
            for item in FAQItem.objects.filter(is_active=True).order_by('order')
        ]

    # =========================================================================
    # ТЕСТ-ДРАЙВ
    # =========================================================================

    @classmethod
    def create_test_drive_lead(
        cls,
        data: dict,
    ) -> tuple[Optional[ContactForm], Optional[str]]:

        telegram_id = data.get('telegram_id')
        user = cls.get_user(telegram_id) if telegram_id else None

        if user:
            has_active = TestDriveRequest.objects.filter(
                user=user,
                status__in=['new', 'confirmed'],
            ).exists()
            if has_active:
                return None, 'has_active'

        preferred_date = None
        date_str = data.get('preferred_date', '')
        if date_str:
            try:
                preferred_date = datetime.strptime(date_str, '%d.%m.%Y').date()
            except ValueError:
                logger.warning(
                    'create_test_drive_lead: bad date format=%s', date_str,
                )

        message_text = (
            f"Тест-драйв\n"
            f"Модель: {data.get('product_title', '—')}\n"
            f"Дата: {data.get('preferred_date', '—')}\n"
            f"Время: {data.get('preferred_time', '—')}\n"
            f"Город: {data.get('city', '—')}"
        )

        try:
            with transaction.atomic():
                lead = ContactForm.objects.create(
                    name=data.get('name', ''),
                    phone=data.get('phone', ''),
                    region=data.get('region') or data.get('city', ''),
                    product=data.get('product_title', ''),
                    message=message_text,
                    referer='Telegram Bot — Тест-драйв',
                    utm_data=_build_utm('test_drive'),
                    status='new',
                    priority='high',
                )

                product_id = data.get('product_id')
                product = None
                if product_id:
                    product = (
                        Product.objects
                        .filter(id=product_id, is_active=True)
                        .first()
                    )

                if user and preferred_date:
                    TestDriveRequest.objects.create(
                        user=user,
                        product=product,
                        dealer=None,
                        client_name=data.get('name', ''),
                        client_phone=data.get('phone', ''),
                        preferred_date=preferred_date,
                        preferred_time=data.get('preferred_time', ''),
                        status='new',
                    )
                    TelegramUser.objects.filter(pk=user.pk).update(
                        total_requests=F('total_requests') + 1,
                    )

        except Exception as exc:
            logger.error(
                'create_test_drive_lead DB error: %s', exc, exc_info=True,
            )
            return None, 'error'

        cls._fire_and_forget(lead)

        return lead, None

    @classmethod
    def get_active_test_drive(
        cls,
        user: TelegramUser,
    ) -> Optional[TestDriveRequest]:
        return (
            TestDriveRequest.objects
            .filter(user=user, status__in=['new', 'confirmed'])
            .select_related('product')
            .first()
        )

    @classmethod
    def cancel_test_drive(cls, td_id: int, user: TelegramUser) -> bool:
        updated = TestDriveRequest.objects.filter(
            id=td_id,
            user=user,
            status__in=['new', 'confirmed'],
        ).update(status='cancelled')
        return bool(updated)

    # =========================================================================
    # ЛИД
    # =========================================================================

    @classmethod
    def create_lead(
        cls,
        data: dict,
        utm_campaign: str = 'catalog_lead',
    ) -> Optional[ContactForm]:
        try:
            with transaction.atomic():
                lead = ContactForm.objects.create(
                    name=data.get('name', ''),
                    phone=data.get('phone', ''),
                    region=data.get('region', ''),
                    product=data.get('product_title', ''),
                    message=data.get('message', ''),
                    referer=(
                        f"Telegram Bot — {data.get('product_title', '')}".strip(' —')
                    ),
                    utm_data=_build_utm(utm_campaign),
                    status='new',
                    priority='high',
                )
        except Exception as exc:
            logger.error('create_lead DB error: %s', exc, exc_info=True)
            return None

        cls._fire_and_forget(lead)
        return lead
    
    @classmethod
    def _send_to_amocrm(cls, lead: ContactForm) -> None:
        try:
            from main.services.amocrm.lead_sender import LeadSender
            LeadSender.send_lead(lead)
        except Exception as exc:
            logger.error('_send_to_amocrm failed lead#%s: %s', lead.id, exc)

    @classmethod
    def _send_telegram_notify(cls, lead: ContactForm) -> None:
        try:
            from main.services.telegram.notification_sender import (
                TelegramNotificationSender,
            )
            TelegramNotificationSender.send_lead_notification(lead)
        except Exception as exc:
            logger.error('_send_telegram_notify failed lead#%s: %s', lead.id, exc)
    # =========================================================================
    # ИЗБРАННОЕ
    # =========================================================================

    @classmethod
    def toggle_wishlist(cls, user: TelegramUser, product_id: int) -> bool:
        obj, created = ProductWishlist.objects.get_or_create(
            user=user,
            product_id=product_id,
        )
        if not created:
            obj.delete()
            return False
        return True

    @classmethod
    def get_wishlist(cls, user: TelegramUser, language: str) -> list[dict]:
        items = (
            ProductWishlist.objects
            .filter(user=user)
            .select_related('product')
            .order_by('-created_at')
        )
        return [
            {
                'id':         item.product.id,
                'title':      _field(item.product, 'title', language),
                'slug':       item.product.slug,
                'image_path': _image_path(
                    item.product.card_image or item.product.main_image
                ),
            }
            for item in items
            if item.product is not None and item.product.is_active
        ]

    # =========================================================================
    # ИСТОРИЯ ПРОСМОТРОВ
    # =========================================================================

    @classmethod
    def record_product_view(cls, user: TelegramUser, product_id: int) -> None:
        obj, created = ProductViewHistory.objects.get_or_create(
            user=user,
            product_id=product_id,
        )
        if not created:
            # F() защищает от race condition
            ProductViewHistory.objects.filter(pk=obj.pk).update(
                view_count=F('view_count') + 1,
            )
            obj.refresh_from_db(fields=['view_count'])
            if obj.view_count >= 3 and user.status == 'new':
                TelegramUser.objects.filter(pk=user.pk).update(status='interested')

    @classmethod
    def get_recent_views(
        cls,
        user: TelegramUser,
        language: str,
        limit: int = 5,
    ) -> list[dict]:
        items = (
            ProductViewHistory.objects
            .filter(user=user)
            .select_related('product')
            .order_by('-last_viewed')[:limit]
        )
        return [
            {
                'id':    item.product.id,
                'title': _field(item.product, 'title', language),
                'slug':  item.product.slug,
            }
            for item in items
            if item.product is not None and item.product.is_active
        ]

    # =========================================================================
    # РАССЫЛКИ
    # =========================================================================

    @classmethod
    def get_pending_broadcasts(cls):
        return BotBroadcast.objects.filter(_q_broadcast_ready(timezone.now()))

    @classmethod
    def get_broadcast_recipients(cls, broadcast: BotBroadcast):
        qs = TelegramUser.objects.filter(
            is_blocked=False,
            notifications_enabled=True,
        )
        filters = {
            'all':       Q(),
            'ru':        Q(language='ru'),
            'uz':        Q(language='uz'),
            'en':        Q(language='en'),
            'hot':       Q(status__in=['hot', 'vip']),
            'vip':       Q(status='vip'),
            'active_30': Q(
                last_active__gte=timezone.now() - timedelta(days=30),
            ),
        }
        if broadcast.target in filters:
            return qs.filter(filters[broadcast.target])
        if broadcast.target == 'region' and broadcast.target_region:
            return qs.filter(region=broadcast.target_region)
        return qs

    @classmethod
    def mark_broadcast_done(cls, broadcast: BotBroadcast, stats: dict) -> None:
        BotBroadcast.objects.filter(pk=broadcast.pk).update(
            status='done',
            total_recipients=stats.get('total', 0),
            sent_count=stats.get('sent', 0),
            failed_count=stats.get('failed', 0),
            blocked_count=stats.get('blocked', 0),
            sent_at=timezone.now(),
        )

    # =========================================================================
    # КОНТАКТЫ
    # =========================================================================

    @classmethod
    def get_contacts(cls) -> BotContacts:
        cached = cache.get('bot_contacts')
        if cached is not None:
            return cached
        contacts = BotContacts.get_instance()
        cache.set('bot_contacts', contacts, timeout=_CONFIG_CACHE_TTL)
        return contacts