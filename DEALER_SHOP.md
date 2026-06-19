# Дилерский магазин запчастей — техническая документация

Этот документ описывает архитектуру, логику работы и защитные механизмы магазина запчастей для дилеров FAW. Магазин полностью изолирован от админки Django и работает на собственной системе аутентификации.

---

## Оглавление

1. [Архитектура и роли](#1-архитектура-и-роли)
2. [Аутентификация (отдельная от админки)](#2-аутентификация-отдельная-от-админки)
3. [Декораторы доступа](#3-декораторы-доступа)
4. [Каталог и корзина](#4-каталог-и-корзина)
5. [Чекаут → черновик → подтверждение](#5-чекаут--черновик--подтверждение)
6. [Списание склада (атомарность, гонки)](#6-списание-склада-атомарность-гонки)
7. [Нумерация счетов (сквозная по году)](#7-нумерация-счетов-сквозная-по-году)
8. [Снапшотинг данных](#8-снапшотинг-данных)
9. [Жизненный цикл заказа (статусы)](#9-жизненный-цикл-заказа-статусы)
10. [Изоляция дилеров](#10-изоляция-дилеров)
11. [Сотрудники: сервис и бухгалтер](#11-сотрудники-сервис-и-бухгалтер)
12. [Защита и безопасность](#12-защита-и-безопасность)
13. [URLs](#13-urls)
14. [Модели данных](#14-модели-данных)
15. [Edge cases и поведение в краевых условиях](#15-edge-cases-и-поведение-в-краевых-условиях)

---

## 1. Архитектура и роли

Магазин — отдельный набор views/templates под URL-префиксом `/dealer/` и `/staff/`. У него **три роли** через `DealerProfile.role`:

| Роль | Значение в БД | Что может |
|------|---------------|-----------|
| Дилер | `dealer` | Покупает: каталог → корзина → черновик → подтверждение. Подтверждает получение. |
| Сотрудник сервиса | `service` | Видит все заказы. Меняет статус `Оплачено → В пути`. Управляет остатками запчастей. |
| Бухгалтер | `accountant` | Видит все заказы. Только подтверждает оплату: `Ожидание → Оплачено`. |

Дефолт при создании учётки — `dealer`. Управление ролями — через админ-форму `DealerProfileAdminForm`.

**Изоляция мира**: магазин не пересекается с обычным сайтом FAW и админкой Django. Юр.лицо и админ-пользователь могут существовать параллельно с дилерским аккаунтом без конфликтов.

---

## 2. Аутентификация (отдельная от админки)

**Принципиальная развязка**: дилерский кабинет НЕ использует Django session/auth_login. Иначе бы вход в дилерку выкидывал из админки и наоборот — мы это уже проходили и сознательно избавились.

### Кука `dealer_sid`

```python
DEALER_COOKIE_NAME    = 'dealer_sid'
DEALER_COOKIE_MAX_AGE = 60 * 60 * 8   # 8 часов
DEALER_COOKIE_SALT    = 'main.dealer-auth.v1'
```

**Содержимое cookie**: подписанный JSON `{"pid": <profile_id>}` через `django.core.signing.dumps()`. Подделать невозможно без знания `SECRET_KEY`.

**Параметры cookie**:
- `HttpOnly` — JS-код её не достанет (защита от XSS-кражи)
- `SameSite=Lax` — cross-site POST не присылают её (CSRF-защита базовая)
- `Secure` — на проде (когда `DEBUG=False`) — только HTTPS

### Проверка пароля

`authenticate(username, password)` — обычный Django backend поверх `auth_user`. Пароль валидируется штатно, но Django session НЕ создаётся. Только устанавливаем свой подписанный cookie.

### Чтение cookie

`_get_dealer_profile_from_request(request)`:
1. Берёт cookie из request
2. Проверяет подпись + не истёк ли (`max_age` встроен в подпись)
3. Тянет `DealerProfile` по `pid`, фильтрует `is_active=True`, проверяет `user.is_active`
4. Возвращает Profile или None

Каждый запрос — фреш-чек из БД. Это значит: **деактивация дилера в админке = мгновенный logout на следующем клике** (а не через 8 часов).

### Смена пароля

POST `/dealer/change-password/` через модалку в кабинете:
- Текущий пароль обязателен (`user.check_password()`)
- Новый прогоняется через Django `validate_password()` (минимум 8, не common, не похож на username)
- После смены — cookie `dealer_sid` остаётся валидным (в нём только profile_id, пароль не хранится). Юзер не вылетает.

---

## 3. Декораторы доступа

В `views.py`:

```python
@dealer_required      # только role=dealer
@service_required     # только role=service
@accountant_required  # только role=accountant
@staff_required       # service ИЛИ accountant
```

**Поведение при «не тот раздел»**: вместо logout — мягкий редирект в собственный landing (`_landing_url_for(profile)`):
- Дилер → `/dealer/`
- Сервис/Бухгалтер → `/staff/orders/`

Так дилер случайно зайдя на `/staff/parts/` не вылетит, а просто увидит свой магазин.

---

## 4. Каталог и корзина

### Каталог

`GET /dealer/` — `dealer_shop`. Показывает активные `SparePart` с фильтрами:
- `?q=` — поиск по артикулу/имени/`name_ru`
- `?truck=ID` — фильтр по грузовику (только если `isdigit()` — защита от мусора в querystring)
- `?type=ID` — фильтр по типу запчасти

Селекты «грузовик» и «тип» — показывают только сущности, у которых **есть** активные запчасти (через `parts__is_active=True`).

### Карточка детали

`GET /dealer/part/<id>/` — `dealer_part_detail`. Полная инфа + блок «Похожие запчасти» (тот же тип ИЛИ тот же грузовик, fallback на 4 свежих).

### Корзина

**Хранилище — localStorage** (`dealer_cart_v1`). Структура: `[{id, qty}, ...]`. Никакого серверного состояния, чтобы:
- Дешёвая запись/чтение
- Не зависит от cookie-сессии

**JS-модуль**: `main/static/js/dealer-cart.js` — singleton `window.DealerCart` с методами `add/setQuantity/remove/clear/count/bindBadge`. При любом изменении бросает событие `dealer-cart-change` (для счётчика-бейджа в header'е).

**Меж-вкладочная синхронизация**: подписка на `window.storage` — если в другой вкладке поменяли корзину, бейдж и страница обновятся.

**Серверная часть**: `GET /dealer/api/cart-parts/?ids=1,2,3` отдаёт JSON с актуальной инфой по выбранным запчастям (имя, цена, остаток на складе, фото). Это для рендера страницы корзины — её содержимое полностью клиентское, JS подтягивает данные.

**Автокоррекция корзины**: при загрузке страницы корзины JS:
- Отбрасывает ID которых нет на сервере (запчасть удалена/деактивирована)
- Обрезает `qty` если оно больше `quantity_available` (закончилась)
- Записывает результат обратно в localStorage

---

## 5. Чекаут → черновик → подтверждение

Двухшаговый процесс. **Цель**: дилер видит реальный документ перед тем как взять обязательства; передумает — ничего не остаётся в БД.

### Шаг 1 — `POST /dealer/cart/checkout/`

`dealer_cart_checkout`:
1. Проверяет реквизиты дилера (`company_name` / `inn` / `contract_number`). Если пусто — 400 «Реквизиты не заполнены, свяжитесь с админом».
2. Парсит JSON `{"items": [{id, qty}, ...]}`. Дубли ID сворачиваются в сумму.
3. Тянет активные запчасти по этим ID.
4. **Удаляет старые черновики этого дилера** (`number__isnull=True`) — 1 черновик за раз.
5. Создаёт `Invoice` с `year=None, number=None` (= черновик).
6. Создаёт `InvoiceItem` с снапшотом цены/имени. `qty` обрезается по `min(requested, stock_available)`.
7. **Склад НЕ списывается** — это специально, чтобы при отмене ничего не возвращать.
8. Считает `total_amount`.
9. Возвращает `{ok: true, redirect_url: '/dealer/invoice/<id>/?from=checkout'}`.

Корзина в localStorage **НЕ чистится** — если дилер передумает и отменит, корзина останется как была.

### Шаг 2 — превью документа

`GET /dealer/invoice/<id>/?from=checkout`:
- Видит **оранжевый баннер** «Предварительный просмотр. Проверьте позиции и нажмите Подтвердить».
- Видит полный документ как при печати (заголовок, реквизиты, таблица, итого, сумма прописью, подписи).
- Две кнопки:
  - **← Отменить** → `POST /dealer/invoice/<id>/cancel/` → удаление черновика → `/dealer/cart/` (корзина на месте).
  - **✓ Подтвердить заказ** → `POST /dealer/invoice/<id>/confirm/` (см. ниже).

### Шаг 3 — `POST /dealer/invoice/<id>/confirm/`

`dealer_invoice_confirm`. **Здесь происходит всё реальное**, атомарно в одной транзакции:

```python
with transaction.atomic():
    # 1. Lock черновика чтобы дважды не подтвердить
    invoice = Invoice.objects.select_for_update().filter(
        id=invoice_id, dealer=profile, number__isnull=True
    ).first()
    if not invoice: return 404

    # 2. Lock всех запчастей, которые будем списывать
    parts_locked = SparePart.objects.select_for_update().filter(
        id__in=item_part_ids
    )

    # 3. Валидация остатков (после lock — гарантия что не уйдём в минус)
    for it in items:
        if part.quantity < it.quantity: return 400 "Недостаточно X"

    # 4. Списание через F() — атомарный SQL UPDATE quantity = quantity - N
    for it in items:
        SparePart.objects.filter(id=it.part_id).update(
            quantity=F('quantity') - it.quantity
        )

    # 5. Lock последнего счёта этого года → присвоение номера
    last = Invoice.objects.select_for_update().filter(
        year=year, number__isnull=False
    ).order_by('-number').first()
    next_number = (last.number + 1) if last else 1

    invoice.year = year
    invoice.number = next_number
    invoice.confirmed_at = timezone.now()
    invoice.save(update_fields=[...])
```

После успеха:
- JS чистит `localStorage` (`DealerCart.clear()`)
- Редирект на `/dealer/invoice/<id>/?from=confirm` → видит **зелёный** «✓ Счёт №3/2026 подтверждён»

---

## 6. Списание склада (атомарность, гонки)

**Защита от гонок** — несколько слоёв:

### Уровень 1 — `transaction.atomic()`

Любая ошибка внутри транзакции откатывает всё. Если списали 5 единиц одной запчасти, но упали на второй — первое списание тоже откатится.

### Уровень 2 — `select_for_update()`

Pessimistic locking. Когда один confirm берёт запчасть в лок, другой confirm ждёт пока первая транзакция закоммитит.

**Что блокируем**:
- Черновик `Invoice` — чтоб 2 параллельных запроса не подтвердили один и тот же
- Все `SparePart` из позиций — чтоб 2 разных заказа не списали один и тот же остаток дважды
- Последний `Invoice` года — чтоб нумерация не дала дубли

### Уровень 3 — `F()` expression

```python
SparePart.objects.filter(id=part_id).update(
    quantity=F('quantity') - it.quantity
)
```

Это `UPDATE … SET quantity = quantity - N WHERE id = X` — атомарный SQL без race condition между read и write. Никаких `obj.quantity -= N; obj.save()` (где между чтением и записью другой процесс может встрять).

### Уровень 4 — DB-уровневые constraints

```python
class Invoice(Meta):
    constraints = [
        UniqueConstraint(fields=['year', 'number'],
                         name='invoice_year_number_unique'),
    ]
```

Даже если все 3 уровня выше каким-то чудом дали два одинаковых номера — PostgreSQL швырнёт `IntegrityError` и второй коммит провалится. Клиент получит 409 «Попробуйте ещё раз».

### Списание в staff (изменение остатка)

`POST /staff/parts/<id>/quantity/` — сервис ставит новое значение остатка (например при поступлении товара):
- `select_for_update()` на запчасти — чтоб два сервисника не перетёрли друг друга
- Поддерживает 2 формата: `{quantity: N}` (установить) или `{delta: ±N}` (прирост/убыль)
- Запрещает уход в минус: `new_val < 0` → 400

---

## 7. Нумерация счетов (сквозная по году)

**Бизнес-правило**: каждый год нумерация начинается с 1. Дилер A заказал первым → №1, дилер B следующим → №2, и т.д.

### Реализация

```python
year = timezone.now().year
last = Invoice.objects.select_for_update().filter(
    year=year, number__isnull=False
).order_by('-number').first()
next_number = (last.number + 1) if last else 1
```

- Фильтр `year=year` — берём только этот год
- `number__isnull=False` — игнорируем черновики (у них номера нет)
- `select_for_update()` — блокируем строку, чтобы параллельные транзакции получили разные номера
- Если ни одного счёта в этом году нет — `next_number = 1`

### Сброс по году

В январе 2027:
- Первый confirm → `last = None` (для 2027 пусто) → `next_number = 1` → счёт `№1/2027`
- Старые счета 2026 продолжают существовать со своими номерами `№N/2026`

### Защита от теоретической гонки

`UniqueConstraint(year, number)` на уровне БД. Даже если 2 транзакции каким-то чудом пройдут lock одновременно — вторая упадёт с `IntegrityError`. Клиент получит 409 и повторит.

---

## 8. Снапшотинг данных

Счёт = документ, фиксирующий состояние на момент выписки. После confirm любое изменение исходных данных НЕ должно ломать старые счета.

### В `Invoice`

```python
buyer_company_name    = CharField   # копия DealerProfile.company_name
buyer_inn             = CharField   # копия DealerProfile.inn
buyer_contract_number = CharField   # копия DealerProfile.contract_number
total_amount          = Decimal     # посчитан по ценам этого момента
```

Если дилер потом сменит юр.название или ИНН — старые счета **останутся со старыми реквизитами**.

### В `InvoiceItem`

```python
part      = FK SET_NULL    # ссылка для аналитики
name      = CharField      # снапшот name_ru или name
quantity  = PositiveIntField
unit      = CharField (default 'шт')
price     = Decimal        # снапшот SparePart.price
sum       = Decimal        # quantity × price (зафиксировано)
```

Если запчасть подорожает или переименуется — старый счёт продолжит показывать исходные значения. `part_id` остаётся (для аналитики — какая модель), но **не используется** при рендере счёта.

`on_delete=SET_NULL` — если запчасть удалят, FK обнулится, но имя/цена/сумма в `InvoiceItem` останутся.

---

## 9. Жизненный цикл заказа (статусы)

### 4 статуса

| Код | Лейбл | Цвет |
|-----|-------|------|
| `pending_payment` | Ожидание оплаты | 🟠 оранжевый |
| `paid` | Оплачено | 🟢 зелёный |
| `in_transit` | В пути | 🔵 синий |
| `delivered` | Доставлено | ⚫ серый |

### Матрица переходов

```python
ALLOWED_STATUS_TRANSITIONS = {
    'accountant': { 'pending_payment': ['paid'] },
    'service':    { 'paid':            ['in_transit'] },
    'dealer':     { 'in_transit':      ['delivered'] },
}
```

**Цепочка прохождения**:

```
[Дилер создаёт + подтверждает]
         ↓
   pending_payment
         ↓  ← Бухгалтер (POST /staff/orders/<id>/status/)
       paid
         ↓  ← Сервис (POST /staff/orders/<id>/status/)
   in_transit
         ↓  ← Дилер у себя в счёте (POST /dealer/invoice/<id>/received/)
    delivered
```

### Защита переходов

`staff_change_status` и `dealer_invoice_mark_received` валидируют:
- Чей счёт (дилер — только свой; staff — любой)
- Подходит ли текущий статус
- Подходит ли роль для этого перехода

Любая попытка перепрыгнуть (например сервис в pending_payment → paid) → 403.

### Ключевой момент: дилер сам подтверждает доставку

Это не сервис ставит «Доставлено». Сервис ставит «В пути», а **дилер у себя в счёте** жмёт «✓ Я получил». Это значит — пока дилер не подтвердит, заказ висит в `in_transit`, и сервис не может схалтурить и поставить «доставлено» сам.

---

## 10. Изоляция дилеров

### Списки

`dealer_invoices_list`:
```python
Invoice.objects.filter(dealer=profile, number__isnull=False)
```
Каждый дилер видит **только свои подтверждённые счета**. Черновики скрыты (они недолговечные).

### Детальный просмотр

`dealer_invoice(request, invoice_id)`:
```python
Invoice.objects.filter(id=invoice_id, dealer=profile)
```
Чужой счёт по прямому URL не открыть — фильтр по `dealer=profile`. Будет «Счёт не найден» (404 → redirect на каталог).

### Действия

`dealer_invoice_confirm`, `dealer_invoice_cancel`, `dealer_invoice_mark_received` — все фильтруют `dealer=profile`. Чужой ID → 404.

---

## 11. Сотрудники: сервис и бухгалтер

### Общий заголовок (нав-табы)

```
[VUM logo]   [Заказы]  [Запчасти]?  [👤 имя · РОЛЬ]
```

«Запчасти» показывается только если `profile.is_service` (бухгалтеру не нужно).

### Список заказов `/staff/orders/`

Доступно обоим. Показывает **все подтверждённые** счета всех дилеров:
- `Invoice.objects.filter(number__isnull=False).order_by('-confirmed_at')[:200]`
- Фильтры: `?status=`, `?q=` (по номеру / имени дилера / ИНН компании)

Поиск по номеру — если строка цифры, ищем `number=int(q)`; иначе по имени/ИНН.

### Детальный просмотр заказа `/staff/orders/<id>/`

Карточки:
1. Управление статусом — кнопки доступных переходов или подсказка («Сначала бухгалтер должен подтвердить оплату», «Заказ в пути — дилер сам подтвердит», «Заказ завершён»).
2. Покупатель (снапшот)
3. Позиции + итого + сумма прописью
4. **«📄 Открыть документ»** → полный счёт-фактура (тот же что у дилера, но без кнопки «Я получил», с навигацией «← К управлению заказом»)

### Список запчастей `/staff/parts/` (только сервис)

Stepper на каждой запчасти. После изменения числа появляется зелёная кнопка «Сохранить» → `POST /staff/parts/<id>/quantity/`. Защита от ухода в минус — на сервере.

---

## 12. Защита и безопасность

### Аутентификация

- ✅ Cookie `dealer_sid` подписан `SECRET_KEY` — подделать нельзя
- ✅ `HttpOnly` — JS не достанет (защита от XSS)
- ✅ `SameSite=Lax` — cross-site POST не присылают
- ✅ `Secure` в проде — только HTTPS
- ✅ Cookie живёт 8 часов (встроено в подпись через `max_age`)
- ✅ Live-проверка `is_active` на каждом запросе — деактивация в админке = немедленный logout

### Авторизация

- ✅ Ролевые декораторы `@dealer_required` / `@service_required` / `@accountant_required` / `@staff_required`
- ✅ В каждой view-функции — повторная проверка владения счёта (`filter(dealer=profile)`) или роли через декоратор
- ✅ Запрет ручных переходов статусов между ролями (матрица `ALLOWED_STATUS_TRANSITIONS`)

### CSRF

- ✅ Django CSRF middleware включён (`csrftoken` cookie)
- ✅ Все POST-эндпоинты требуют CSRF-token либо через header `X-CSRFToken`, либо через скрытый form-input
- ✅ Cookie `csrftoken` отдельный от `dealer_sid` — система продолжает работать даже если один из них съел

### XSS

- ✅ Django templates автоэскейпят по умолчанию
- ✅ Description запчасти (CKEditor `text_only`) — без `image/iframe/table` плагинов (защита от инъекций через HTML)
- ✅ `format_html_join` в виджете datalist — автоэкранирование имён типов

### SQL injection

- ✅ Всё через Django ORM. Никаких raw queries.
- ✅ Фильтры по querystring проходят `isdigit()` / `int()` — даже если пихнуть `'1; DROP TABLE'`, оно не пройдёт валидацию

### Гонки (race conditions)

- ✅ `select_for_update()` на черновиках и запчастях при confirm
- ✅ `F()` expressions для списания склада
- ✅ `UniqueConstraint(year, number)` — DB-уровневая защита от дублей нумерации
- ✅ Один черновик за раз (старые удаляются на новом checkout)

### Целостность данных

- ✅ Снапшотинг (`buyer_company_name`, цены в `InvoiceItem`) — старые счета не плывут
- ✅ `on_delete=PROTECT` на `Invoice.dealer` — нельзя удалить дилера с активными счетами
- ✅ `on_delete=SET_NULL` на `InvoiceItem.part` — удаление запчасти не ломает старые счета
- ✅ Подтверждённые счета в админке нельзя удалить (`has_delete_permission` пропускает только черновики)
- ✅ Большинство полей `Invoice` в админке `readonly` — менять можно только статус

### Лимиты загрузки

- ✅ Все `ImageField` ограничены `validate_image_size` = 5 МБ
- ✅ JSON-чекаут обрезает `requested[ids][:100]` — защита от DoS массивом

### Логи

Каждое важное действие логируется через `logger.info`:
- Создание черновика (`Invoice draft created: id=N`)
- Подтверждение (`Invoice confirmed: №N/Y`)
- Отмена (`Invoice draft cancelled: id=N`)
- Смена статуса (`Status changed: invoice=№N/Y by=<user> (<role>) → <new>`)
- Получение дилером (`Invoice received by dealer: №N/Y`)
- Логин/logout, смена пароля
- Изменение остатка (`Stock updated: part=X qty=N by=<user>`)

---

## 13. URLs

### Дилер

| URL | Метод | View | Что |
|-----|-------|------|-----|
| `/dealer/login/` | GET, POST | `dealer_login` | Логин-форма |
| `/dealer/logout/` | POST | `dealer_logout` | Чистит cookie |
| `/dealer/change-password/` | POST | `dealer_change_password` | Смена пароля (AJAX из модалки) |
| `/dealer/` | GET | `dealer_shop` | Каталог запчастей |
| `/dealer/part/<id>/` | GET | `dealer_part_detail` | Детальная запчасти |
| `/dealer/cart/` | GET | `dealer_cart_view` | Корзина (shell, JS рендерит) |
| `/dealer/api/cart-parts/?ids=...` | GET | `dealer_cart_api` | JSON-данные по позициям |
| `/dealer/cart/checkout/` | POST | `dealer_cart_checkout` | Создание черновика |
| `/dealer/invoice/<id>/` | GET | `dealer_invoice` | Документ (черновик или подтверждённый) |
| `/dealer/invoice/<id>/confirm/` | POST | `dealer_invoice_confirm` | Подтверждение черновика |
| `/dealer/invoice/<id>/cancel/` | POST | `dealer_invoice_cancel` | Удаление черновика |
| `/dealer/invoice/<id>/received/` | POST | `dealer_invoice_mark_received` | Я получил → delivered |
| `/dealer/invoices/` | GET | `dealer_invoices_list` | История счетов |

### Сотрудники

| URL | Кто | View | Что |
|-----|-----|------|-----|
| `/staff/orders/` | service+accountant | `staff_orders_list` | Все заказы |
| `/staff/orders/<id>/` | service+accountant | `staff_order_detail` | Управление статусом |
| `/staff/orders/<id>/status/` | POST | `staff_change_status` | Смена статуса (с ролью) |
| `/staff/orders/<id>/document/` | service+accountant | `staff_invoice_view` | Полный документ |
| `/staff/parts/` | service | `staff_parts_list` | Все запчасти |
| `/staff/parts/<id>/quantity/` | POST (service) | `staff_part_update_quantity` | Изменить остаток |

---

## 14. Модели данных

### `DealerProfile`

```python
user                = OneToOne(User)
role                = CharField(choices=['dealer','service','accountant'], default='dealer')
name                = CharField(max_length=200)
avatar              = ImageField (validate_image_size 5MB)
company_name        = CharField(blank=True)   # required-валидация только для роли dealer
inn                 = CharField(blank=True, db_index=True)
contract_number     = CharField(blank=True)
is_active           = Boolean
created_at, updated_at
```

### `SparePart`

```python
part_number        = CharField(unique=True, db_index=True)   # артикул
name               = CharField (модельтрансляция: name_ru/uz/en, required ru)
description        = RichTextField (CKEditor text_only, перевод)
type               = FK SparePartType (PROTECT)
quantity           = PositiveInt   ← вот это списывается на confirm
price              = Decimal(12,2)
truck              = FK Product (SET_NULL, optional) — для фильтра
is_active          = Boolean
created_at, updated_at
```

### `SparePartType`

```python
name               = CharField (модельтрансляция: name_ru/uz/en, required ru)
created_at
```

Хитрый автокомплит в admin-форме: вводишь "Двигатель" → ищем `name_ru__iexact='двигатель'` → если есть, переиспользуем, если нет — создаём.

### `Invoice`

```python
dealer                    = FK DealerProfile (PROTECT)
year                      = PositiveInt (NULL = черновик)
number                    = PositiveInt (NULL = черновик)
confirmed_at              = DateTime (NULL = черновик)

buyer_company_name        = CharField  # снапшот!
buyer_inn                 = CharField
buyer_contract_number     = CharField

total_amount              = Decimal(14,2)
status                    = CharField(choices=4 values, default='pending_payment')

created_at

@property is_draft  →  number is None

constraints: UniqueConstraint(year, number)
```

### `InvoiceItem`

```python
invoice    = FK Invoice (CASCADE)
part       = FK SparePart (SET_NULL, для аналитики)
name       = CharField   # снапшот
quantity   = PositiveInt
unit       = CharField (default 'шт')
price      = Decimal     # снапшот
sum        = Decimal     # qty × price
```

---

## 15. Edge cases и поведение в краевых условиях

### Дилер создаёт черновик и закрывает таб

Черновик остаётся в БД, но **только до следующего checkout этого дилера**. Следующий checkout удалит его (`Invoice.objects.filter(dealer=profile, number__isnull=True).delete()`).

Никакого фонового cleanup нет — это не нужно, потому что каждый дилер держит максимум 1 черновик.

### Запчасть закончилась между checkout и confirm

Сценарий: дилер A набрал 5 единиц, создал черновик. Пока он медлил, дилер B оформил и подтвердил — остаток упал до 2.

При confirm дилера A:
- `select_for_update()` блокирует запчасть
- Видим `part.quantity = 2 < it.quantity = 5`
- Возвращаем 400 с понятным текстом: «Недостаточно X. Доступно: 2, требуется: 5»
- `transaction.atomic()` откатывает, ничего не списано
- Черновик дилера A остаётся — он может отменить и пересобрать корзину

### Запчасть удалили из админки между checkout и confirm

Тот же сценарий, но запчасть полностью удалена:
- `part_id` ещё есть в InvoiceItem, но `part_id` не вернёт строку в `SparePart.objects.filter(...)`
- Считаем что запчасть удалена → 400 «Запчасть удалена из каталога»

### Запчасть деактивирована (`is_active=False`)

В confirm: проверяем `part.is_active`. Если False → 400 «Запчасть больше не доступна».

### Дилер пытается подтвердить чужой черновик

`Invoice.objects.filter(id=X, dealer=profile, number__isnull=True)` → не найдёт → 404.

### Дилер пытается подтвердить уже подтверждённый счёт

Фильтр `number__isnull=True` → не найдёт → 404 «не найден или уже подтверждён».

### Сервис пытается перепрыгнуть статус (например `pending_payment` → `in_transit`)

`_allowed_next_statuses(profile, 'pending_payment')` для service вернёт `[]` → 403 «У вашей роли нет права на этот переход».

### Дилер пытается отметить «получено» когда счёт ещё в `paid`

`Invoice.objects.filter(..., status=in_transit)` → не найдёт → 404 «не в пути».

### Реквизиты дилера пустые при checkout

`if not company_name or not inn or not contract_number: return 400` с сообщением «Свяжитесь с администратором».

### Браузер не поддерживает localStorage

`try/except` в `dealer-cart.js` — корзина не сохранится, но и сайт не сломается. Просто работает как однотразовая (потеряется при перезагрузке).

### Cookie `dealer_sid` истёк (через 8 часов)

`signing.loads()` → `BadSignature` → возвращаем None → декоратор перенаправляет на `/dealer/login/` и чистит cookie через `delete_cookie()`.

### Гонка нумерации (две транзакции пытаются взять номер 5 одновременно)

1. Обе ждут на `select_for_update()` последней строки года
2. Первая получает lock, видит max=4, ставит number=5, коммитит
3. Вторая получает lock, видит max=5, ставит number=6, коммитит

Никаких дублей. Даже если каким-то чудом обе вышли с number=5 — `UniqueConstraint(year, number)` бросит `IntegrityError`, вторая упадёт с 409 «Попробуйте ещё раз».

### Дилер сменил пароль в модалке

`user.set_password(new); user.save(update_fields=['password'])`. Cookie `dealer_sid` **продолжает работать** — в нём только `pid`, не пароль. Никакого forced logout не требуется.

### Удаление подтверждённого счёта

Через админку — запрещено (`has_delete_permission` возвращает True только для черновиков). Если суперюзер удалит через shell — `on_delete=PROTECT` на `Invoice.dealer` сработает только если хотим удалить дилера; для самого Invoice — каскадно удалит `InvoiceItem`, но **склад НЕ восстановит** (намеренно — это документ, его не отменить).

Если нужно «откатить» — это бизнес-процесс, делается отдельным заказом-возвратом (пока не реализован).

### `USE_THOUSAND_SEPARATOR=True` и год счёта

Django по умолчанию рендерит integer в шаблоне с пробелом-разделителем тысяч (`2026` → `2 026`). Поэтому в `views.py` мы передаём `'year': str(invoice.year)` и `'number': str(invoice.number)` — строки Django уже не форматирует.

### Загрузка фото > 5 МБ

`validate_image_size` бросит `ValidationError` ещё в форме. Файл вообще не запишется в `media/`.

### Замена фото или удаление объекта с фото

Сигналы `pre_save` и `post_delete` из `signals_cleanup.py` чистят старые файлы с диска. Без них `media/` копила бы orphans.

---

## Файлы — где что искать

| Слой | Файл |
|------|------|
| Модели магазина | [main/models.py](main/models.py) — `DealerProfile`, `SparePart`, `SparePartType`, `SparePartImage`, `Invoice`, `InvoiceItem` |
| Утилиты форматирования | [main/utils/invoice_format.py](main/utils/invoice_format.py) — `format_uzs`, `format_date_ru`, `amount_in_words_uzs` |
| Валидаторы | [main/validators.py](main/validators.py) — `validate_image_size` |
| Очистка orphan-файлов | [main/signals_cleanup.py](main/signals_cleanup.py) |
| Views (магазин + staff + auth) | [main/views.py](main/views.py) |
| URL-карта | [main/urls.py](main/urls.py) |
| Формы | [main/forms.py](main/forms.py) — `DealerLoginForm`, `DealerProfileAdminForm`, `DealerPasswordChangeForm`, `SparePartAdminForm` |
| Админка | [main/admin.py](main/admin.py) — `DealerProfileAdmin`, `SparePartAdmin`, `SparePartTypeAdmin`, `InvoiceAdmin` |
| Шаблоны дилера | `main/templates/main/dealer/`: `login.html`, `shop.html`, `shop_detail.html`, `cart.html`, `invoice.html`, `invoices_list.html`, `_profile_modal.html` |
| Шаблоны staff | `main/templates/main/dealer/`: `staff_orders.html`, `staff_order_detail.html`, `staff_parts.html` |
| JS-корзина | [main/static/js/dealer-cart.js](main/static/js/dealer-cart.js) |
