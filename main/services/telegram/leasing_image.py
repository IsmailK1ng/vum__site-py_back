import io
from datetime import date
from PIL import Image, ImageDraw, ImageFont

_NAVY   = (26,  54,  93)   
_WHITE  = (255, 255, 255)
_LIGHT  = (245, 247, 250)  
_DARK   = (30,  30,  30)   
_GRAY   = (120, 120, 120)  
_YELLOW = (255, 193,  7)   
_GREEN  = (26,  54,  93)   

_W = 860 

_FONT_CANDIDATES = ['arial.ttf', 'Arial.ttf', 'DejaVuSans.ttf', 'FreeSans.ttf']

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    bold_candidates = ['arialbd.ttf', 'Arial Bold.ttf', 'DejaVuSans-Bold.ttf', 'FreeSansBold.ttf']
    candidates = bold_candidates if bold else _FONT_CANDIDATES
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()



def _fmt(n: int) -> str:
    return f"{n:,}".replace(',', ' ')


def _text_width(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _draw_rect(draw: ImageDraw.Draw, x1: int, y1: int, x2: int, y2: int, color: tuple) -> None:
    draw.rectangle([x1, y1, x2, y2], fill=color)


def _centered_text(
    draw: ImageDraw.Draw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    color: tuple = _WHITE,
    width: int = _W,
) -> None:
    tw = _text_width(draw, text, font)
    draw.text(((width - tw) // 2, y), text, font=font, fill=color)



def _amortization_schedule(financing: int, annual_rate: float, term: int, monthly: int) -> list[dict]:
    mr = annual_rate / 12
    balance = financing
    rows = []
    for month in range(1, term + 1):
        interest = round(balance * mr)
        principal = monthly - interest
        balance -= principal
        rows.append({
            'month':     month,
            'principal': principal,
            'interest':  interest,
            'payment':   monthly,
            'balance':   max(balance, 0),
        })
    return rows


def _draw_page1(
    draw: ImageDraw.Draw,
    calc: dict,
    title: str,
    lang: str,
    y_start: int,
) -> int:
    """Рисует страницу 1. Возвращает y после последнего элемента."""
    cur = {'ru': 'сум', 'uz': "so'm", 'en': 'UZS'}.get(lang, "so'm")
    ml  = {'ru': 'мес', 'uz': 'oy',   'en': 'mo'}.get(lang, 'oy')

    f_title  = _load_font(22, bold=True)
    f_sub    = _load_font(14)
    f_body   = _load_font(15)
    f_bold   = _load_font(15, bold=True)
    f_big    = _load_font(36, bold=True)
    f_medium = _load_font(18, bold=True)
    f_small  = _load_font(12)

    PAD = 30
    y = y_start

    _draw_rect(draw, 0, y, _W, y + 100, _NAVY)
    _centered_text(draw, 'VUM/FAW TRUCKS', y + 12, _load_font(26, bold=True))
    _centered_text(draw, "O'zbekistondagi rasmiy dilyer", y + 48, f_sub)
    _centered_text(draw, f'faw.uz | +998 (55) 508-60-60', y + 68, f_sub)
    y += 100

    lizing_label = {
        'ru': 'РАСЧЁТ ЛИЗИНГА',
        'uz': 'LIZING HISOBLASH',
        'en': 'LEASING CALCULATION',
    }.get(lang, 'LIZING HISOBLASH')
    date_label = {'ru': 'Дата', 'uz': 'Sana', 'en': 'Date'}.get(lang, 'Sana')
    today_str = date.today().strftime('%d.%m.%Y')

    y += 20
    _centered_text(draw, lizing_label, y, f_title, color=_NAVY)
    y += 36
    _centered_text(draw, f"{date_label}: {today_str}", y, f_sub, color=_GRAY)
    y += 30

    block_h = 80
    _draw_rect(draw, PAD, y, _W - PAD, y + block_h, _NAVY)
    pay_label = {'ru': 'Ежемесячный платёж', 'uz': "Oylik to'lov", 'en': 'Monthly payment'}.get(lang, "Oylik to'lov")
    _centered_text(draw, pay_label, y + 10, f_sub)
    _centered_text(draw, f"{_fmt(calc['monthly_payment'])} {cur}", y + 30, f_big)
    y += block_h + 20

    param_label  = {'ru': 'Параметр',  'uz': 'Parametr', 'en': 'Parameter'}.get(lang, 'Parametr')
    value_label  = {'ru': 'Значение',  'uz': 'Qiymati',  'en': 'Value'}.get(lang, 'Qiymati')

    col1_w = 340
    _draw_rect(draw, PAD, y, PAD + col1_w, y + 36, _NAVY)
    _draw_rect(draw, PAD + col1_w, y, _W - PAD, y + 36, _NAVY)
    draw.text((PAD + 10, y + 9), param_label, font=f_bold, fill=_WHITE)
    draw.text((PAD + col1_w + 10, y + 9), value_label, font=f_bold, fill=_WHITE)
    y += 36

    rows_labels = {
        'ru': [
            ('Модель техники',       title),
            ('Цена техники',         f"{_fmt(calc['price'])} {cur}"),
            ('Первоначальный взнос', f"{_fmt(calc['down_payment'])} {cur} ({calc['down_pct']}%)"),
            ('Сумма финансирования', f"{_fmt(calc['financing'])} {cur}"),
            ('Срок лизинга',         f"{calc['term']} {ml}"),
            ('Процентная ставка',    f"{calc['annual_rate'] * 100:.1f}% годовых"),
            ('Общая сумма выплат',   f"{_fmt(calc['total_payment'])} {cur}"),
            ('Доп. расходы (0.5%)',  f"{_fmt(calc['financing'] - (calc['price'] - calc['down_payment']))} {cur}"),
            ('Итоговая сумма',       f"{_fmt(calc['down_payment'] + calc['total_payment'])} {cur}"),
        ],
        'uz': [
            ('Texnika nomi',         title),
            ('Texnika narxi',        f"{_fmt(calc['price'])} {cur}"),
            ("Dastlabki to'lov",     f"{_fmt(calc['down_payment'])} {cur} ({calc['down_pct']}%)"),
            ('Moliyalashtirish summasi', f"{_fmt(calc['financing'])} {cur}"),
            ('Lizing muddati',       f"{calc['term']} {ml}"),
            ('Foiz stavkasi',        f"{calc['annual_rate'] * 100:.1f}% yillik"),
            ("Jami to'lovlar",       f"{_fmt(calc['total_payment'])} {cur}"),
            ("Qo'shimcha (foizlar)", f"{_fmt(calc['financing'] - (calc['price'] - calc['down_payment']))} {cur}"),
            ('Umumiy summa',         f"{_fmt(calc['down_payment'] + calc['total_payment'])} {cur}"),
        ],
        'en': [
            ('Model',                title),
            ('Price',                f"{_fmt(calc['price'])} {cur}"),
            ('Down payment',         f"{_fmt(calc['down_payment'])} {cur} ({calc['down_pct']}%)"),
            ('Financing amount',     f"{_fmt(calc['financing'])} {cur}"),
            ('Lease term',           f"{calc['term']} {ml}"),
            ('Annual rate',          f"{calc['annual_rate'] * 100:.1f}%"),
            ('Total payments',       f"{_fmt(calc['total_payment'])} {cur}"),
            ('Additional costs',     f"{_fmt(calc['financing'] - (calc['price'] - calc['down_payment']))} {cur}"),
            ('Grand total',          f"{_fmt(calc['down_payment'] + calc['total_payment'])} {cur}"),
        ],
    }

    rows = rows_labels.get(lang, rows_labels['uz'])
    row_h = 38
    for i, (param, value) in enumerate(rows):
        bg = _LIGHT if i % 2 == 0 else _WHITE
        _draw_rect(draw, PAD, y, _W - PAD, y + row_h, bg)
        draw.text((PAD + 10, y + 10), param, font=f_body, fill=_DARK)
        vw = _text_width(draw, value, f_bold)
        draw.text((_W - PAD - vw - 10, y + 10), value, font=f_bold, fill=_DARK)
        y += row_h

    y += 20

    conditions = {
        'ru': [
            ("Минимальный взнос — 0%",     "Техника становится вашей"),
            ("Максимальный срок — 60 мес", "Без кредитной истории"),
            ("Быстрое оформление (1-2 дня)", "КАСКО страхование обязательно"),
            ("Досрочное погашение",          "Индивидуальный подход"),
        ],
        'uz': [
            ("Minimal to'lov — 0% dan",    "Texnika sizniki bo'ladi"),
            ("Maksimal muddat — 60 oy",     "Kredit tarixisiz"),
            ("Tez rasmiylashtirish (1-2 kun)", "KASKO sug'urta majburiy"),
            ("Muddatidan oldin to'lash",    "Individual yondashuv"),
        ],
        'en': [
            ("Minimum down — 0%",          "Equipment becomes yours"),
            ("Maximum term — 60 months",   "No credit history needed"),
            ("Fast processing (1-2 days)", "KASKO insurance required"),
            ("Early repayment available",  "Individual approach"),
        ],
    }

    cond_title = {'ru': 'Условия лизинга', 'uz': 'Lizing shartlari', 'en': 'Leasing terms'}.get(lang, 'Lizing shartlari')
    _draw_rect(draw, PAD, y, PAD + 4, y + 16, _YELLOW)
    draw.text((PAD + 14, y), cond_title, font=f_medium, fill=_NAVY)
    y += 30

    cond_list = conditions.get(lang, conditions['uz'])
    col_w = (_W - PAD * 2) // 2
    for i in range(0, len(cond_list), 2):
        left  = cond_list[i]
        right = cond_list[i + 1] if i + 1 < len(cond_list) else ('', '')
        draw.text((PAD, y),           f"• {left[0]}",  font=f_small, fill=_DARK)
        draw.text((PAD + col_w, y),   f"• {right[0]}", font=f_small, fill=_DARK)
        y += 20

    y += 20

    note = {
        'ru': 'Важно: данный расчёт является предварительным. Уточняйте условия у менеджера.',
        'uz': "Muhim: Ushbu hisob-kitob dastlabki. Yakuniy shartlarni menejer bilan aniqlang.",
        'en': 'Important: This is a preliminary calculation. Confirm terms with a manager.',
    }.get(lang, "Muhim: Ushbu hisob-kitob dastlabki.")

    _draw_rect(draw, PAD, y, _W - PAD, y + 34, (255, 248, 220))
    _draw_rect(draw, PAD, y, PAD + 4, y + 34, _YELLOW)
    draw.text((PAD + 14, y + 9), note, font=f_small, fill=(100, 80, 0))
    y += 50

    return y


def _draw_page2(
    draw: ImageDraw.Draw,
    calc: dict,
    lang: str,
    y_start: int,
) -> int:
    cur = {'ru': 'сум', 'uz': "so'm", 'en': 'UZS'}.get(lang, "so'm")
    ml  = {'ru': 'мес', 'uz': 'oy',   'en': 'mo'}.get(lang, 'oy')

    f_bold  = _load_font(14, bold=True)
    f_body  = _load_font(13)
    f_title = _load_font(20, bold=True)
    f_sub   = _load_font(13)

    PAD = 30
    y = y_start + 30

    table_title = {
        'ru': 'График платежей',
        'uz': "Oylik to'lovlar jadvali",
        'en': 'Payment Schedule',
    }.get(lang, "Oylik to'lovlar jadvali")
    rate_str = f"{calc['annual_rate'] * 100:.1f}%"
    subtitle = f"Muddat: {calc['term']} {ml} | Stavka: {rate_str}"

    _centered_text(draw, table_title, y, f_title, color=_NAVY)
    y += 30
    _centered_text(draw, subtitle, y, f_sub, color=_GRAY)
    y += 30

    headers = {
        'ru': ['#', 'Осн. долг', 'Проценты', 'Платёж', 'Остаток'],
        'uz': ['#', 'Asosiy qarz', 'Foizlar', "To'lov", 'Qoldiq'],
        'en': ['#', 'Principal', 'Interest', 'Payment', 'Balance'],
    }.get(lang, ['#', 'Asosiy qarz', 'Foizlar', "To'lov", 'Qoldiq'])

    col_widths = [50, 185, 155, 155, 185]  # итого 730 = _W - 2*PAD
    col_x = [PAD + sum(col_widths[:i]) for i in range(len(col_widths))]

    row_h = 28
    _draw_rect(draw, PAD, y, _W - PAD, y + row_h, _NAVY)
    for i, (hdr, cx) in enumerate(zip(headers, col_x)):
        if i == 0:
            draw.text((cx + 8, y + 7), hdr, font=f_bold, fill=_WHITE)
        else:
            hw = _text_width(draw, hdr, f_bold)
            cx_right = col_x[i] + col_widths[i] - 8
            draw.text((cx_right - hw, y + 7), hdr, font=f_bold, fill=_WHITE)
    y += row_h

    schedule = _amortization_schedule(
        financing=calc['financing'],
        annual_rate=calc['annual_rate'],
        term=calc['term'],
        monthly=calc['monthly_payment'],
    )

    total_principal = 0
    total_interest  = 0
    total_payment   = 0

    for row in schedule:
        bg = _LIGHT if row['month'] % 2 == 0 else _WHITE
        _draw_rect(draw, PAD, y, _W - PAD, y + row_h, bg)

        cells = [
            str(row['month']),
            _fmt(row['principal']),
            _fmt(row['interest']),
            _fmt(row['payment']),
            _fmt(row['balance']),
        ]
        for i, (cell, cx) in enumerate(zip(cells, col_x)):
            if i == 0:
                draw.text((cx + 8, y + 7), cell, font=f_body, fill=_DARK)
            else:
                cw = _text_width(draw, cell, f_body)
                draw.text((col_x[i] + col_widths[i] - 8 - cw, y + 7), cell, font=f_body, fill=_DARK)

        total_principal += row['principal']
        total_interest  += row['interest']
        total_payment   += row['payment']
        y += row_h

    jami = {'ru': 'ИТОГО', 'uz': 'JAMI', 'en': 'TOTAL'}.get(lang, 'JAMI')
    _draw_rect(draw, PAD, y, _W - PAD, y + row_h, _NAVY)
    draw.text((col_x[0] + 8, y + 7), jami, font=f_bold, fill=_WHITE)
    for i, val in enumerate([total_principal, total_interest, total_payment, 0], start=1):
        s = _fmt(val) if val > 0 else '0'
        sw = _text_width(draw, s, f_bold)
        draw.text((col_x[i] + col_widths[i] - 8 - sw, y + 7), s, font=f_bold, fill=_WHITE)
    y += row_h

    note = {
        'ru': 'Важно: данный расчёт является предварительным. Уточняйте условия у менеджера.',
        'uz': "Muhim: Ushbu hisob-kitob dastlabki. Yakuniy shartlarni menejer bilan aniqlang.",
        'en': 'Important: This is a preliminary calculation. Confirm terms with a manager.',
    }.get(lang, "Muhim: Ushbu hisob-kitob dastlabki.")

    y += 16
    _draw_rect(draw, PAD, y, _W - PAD, y + 34, (255, 248, 220))
    _draw_rect(draw, PAD, y, PAD + 4, y + 34, _YELLOW)
    f_small = _load_font(12)
    draw.text((PAD + 14, y + 9), note, font=f_small, fill=(100, 80, 0))
    y += 50

    return y



def generate_leasing_image(calc: dict, title: str, lang: str) -> bytes:

    term = calc['term']
    h1 = 950
    h2 = 80 + (term + 1) * 28 + 150
    total_h = h1 + h2 + 40  

    img  = Image.new('RGB', (_W, total_h), color=_WHITE)
    draw = ImageDraw.Draw(img)

    y = _draw_page1(draw, calc, title, lang, y_start=0)


    draw.line([(30, y), (_W - 30, y)], fill=_NAVY, width=2)

    y = _draw_page2(draw, calc, lang, y_start=y)

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return buf.read()