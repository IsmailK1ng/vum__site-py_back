"""Утилиты форматирования счёта на оплату.

- format_uzs(amount) → '1 200 000,00' (узбекский/русский формат: пробел тыс., запятая дроби)
- format_date_ru(dt) → '15 июня 2026' (русский, локальная TZ Asia/Tashkent)
- amount_in_words_uzs(amount) → 'Один миллион двести тысяч сум 00 тийин'
"""

from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

# Месяцы РУ — для формата '15 июня 2026'.
_RU_MONTHS = (
    'января', 'февраля', 'марта', 'апреля',
    'мая', 'июня', 'июля', 'августа',
    'сентября', 'октября', 'ноября', 'декабря',
)


def format_uzs(amount):
    """Сумма → '1 200 000,00'.

    Принимает Decimal/int/float; всегда возвращает строку с двумя знаками
    после запятой, пробелами между тысячами.
    """
    if amount is None:
        return '0,00'
    # До Decimal — чтобы не словить float-погрешности на больших суммах
    d = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    sign = '-' if d < 0 else ''
    d = abs(d)
    int_part, frac_part = divmod(d, 1)
    int_str = f'{int(int_part):,}'.replace(',', ' ')     # 1,200,000 → '1 200 000'
    frac_int = int((frac_part * 100).quantize(Decimal('1')))
    return f'{sign}{int_str},{frac_int:02d}'


def format_date_ru(dt):
    """datetime/date → '15 июня 2026'.

    Если приходит aware-datetime — переводим в локальную TZ (Asia/Tashkent),
    чтобы дата соответствовала ташкентскому дню а не UTC.
    """
    if dt is None:
        return ''
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        dt = timezone.localtime(dt)
    return f'{dt.day} {_RU_MONTHS[dt.month - 1]} {dt.year}'


def amount_in_words_uzs(amount):
    """Сумма прописью для UZS-счёта.

    Пример: Decimal('1200000.00') → 'Один миллион двести тысяч сум 00 тийин'.
    Целая часть — словами на русском (через num2words), тийины — двузначным числом.
    """
    # Импорт здесь — чтоб модуль грузился даже если num2words ещё не установлен.
    from num2words import num2words

    if amount is None:
        amount = 0
    d = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    sum_part = int(d)
    tiyin_part = int((d - sum_part) * 100)

    words = num2words(sum_part, lang='ru')
    words = words[:1].upper() + words[1:]  # capitalize первую букву

    return f'{words} сум {tiyin_part:02d} тийин'
