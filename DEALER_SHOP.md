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
- `?parent=ID` — фильтр по родительской модели (платформе/шасси, M2M `SparePart.parent_models`; только если `isdigit()` — защита от мусора в querystring)
- `?type=ID` — фильтр по типу запчасти
- `?page=N` — пагинация по `SHOP_PAGE_SIZE = 24`; ссылки страниц сохраняют текущие фильтры

Селекты «модель» и «тип» — показывают только сущности, у которых **есть** активные запчасти.

### Карточка детали

`GET /dealer/part/<id>/` — `dealer_part_detail`. Полная инфа + блок «Похожие запчасти» (тот же тип ИЛИ общая родительская модель, fallback на 4 свежих).

Карточку может открыть и **сервис** (сверить фото/описание из `/staff/parts/`) — для него скрыты корзина, история счетов и кнопка «В корзину», а «назад» ведёт в список запчастей staff.

### Корзина

**Хранилище — localStorage**, ключ `dealer_cart_v1_<profile_id>` — своя корзина у каждого дилера (иначе два дилера за одним компьютером видели бы корзину друг друга). id профиля приходит из `<script src="dealer-cart.js" data-owner="{{ profile.id }}">`. Старая общая корзина `dealer_cart_v1` один раз переносится первому зашедшему дилеру и удаляется. Структура: `[{id, qty}, ...]`. Никакого серверного состояния, чтобы:
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

    # 4. Цена изменилась с момента черновика? → пересчитываем черновик,
    #    отвечаем 409 {reload: true}, склад не трогаем. Дилер видит новую сумму
    #    и подтверждает ещё раз. По старой цене подтвердить нельзя.

    # 5. Списание через change_stock() — атомарный UPDATE quantity = quantity - N
    #    + запись в журнал склада StockMovement (reason='order')
    for it in items:
        change_stock(it.part_id, -it.quantity, StockMovement.REASON_ORDER, invoice=invoice, ...)

    # 6. Lock последнего счёта этого года → присвоение номера
    year = timezone.localdate().year     # год по Ташкенту, не по UTC
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

### Журнал склада `StockMovement`

Каждое изменение остатка пишется в журнал: запчасть, `delta` (±N), остаток после, причина, счёт (если есть), кто и когда.

| Причина | Когда пишется |
|---------|---------------|
| `order` | Подтверждение заказа дилером; возврат отменённого заказа в работу из админки |
| `order_cancel` | Отмена заказа — позиции возвращаются на склад |
| `staff` | Сервис меняет остаток на `/staff/parts/` |
| `admin` | Остаток изменён в админке (в карточке, в списке через `list_editable`, или при создании запчасти) |

Код — `change_stock()` (меняет остаток через `F()` + пишет журнал) и `record_stock_change()` (только журнал, если остаток уже сохранён) в `main/models.py`. Смотреть — раздел админки «Магазин — Движение склада» (только чтение) и свёрнутый блок «Движение склада» в карточке запчасти.

---

## 7. Нумерация счетов (по договору дилера)

**Бизнес-правило**: у каждого дилера своя нумерация внутри текущего договора: 1, 2, 3… Номер спецификации = номер счёта (внутри договора, см. раздел 7). Когда подписан новый договор, сервис заводит его в разделе «Договоры» (`/staff/contracts/`): вводит номер и дату, нажимает «↺ Новый договор», и нумерация этого дилера начинается заново с №1, не дожидаясь нового года.

### Модель `DealerContract`

`dealer`, `number`, `date`, `last_number` (последний выданный номер), `created_by`, `created_at`. Текущий договор — самый свежий. Номер/дата текущего договора дублируются в `DealerProfile.contract_number/contract_date`.

- Первый договор заводится автоматически из реквизитов профиля при первом подтверждении (`current_contract()`, `created_by='auto'`).
- Правка номера/даты в админке (учётка дилера) — исправление текущего договора, нумерация **не** сбрасывается.
- В админке «Договоры дилеров» — история, только чтение (номер/дату можно поправить).

### Реализация (в `dealer_invoice_confirm`)

```python
DealerProfile.objects.select_for_update().filter(pk=profile.pk).first()  # сериализует заказы дилера и сброс
contract = current_contract(profile)
contract.last_number += 1
invoice.number = contract.last_number
invoice.contract = contract
invoice.buyer_contract_number/date = contract.number/date   # на момент подтверждения
invoice.year = timezone.localdate().year                    # год остаётся — для фильтров и «№N/2026»
```

Черновик, созданный до нового договора, при подтверждении получит номер и реквизиты нового договора.

### Старые счета

Счета до введения договоров (`contract = NULL`) сохраняют свои номера (сквозные по году).

### Защита от гонки

- `UniqueConstraint(contract, number)` — для новых счетов.
- `UniqueConstraint(year, number) WHERE contract IS NULL` — для старых.
- При `IntegrityError` клиент получает 409 и повторяет.

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
price     = Decimal        # цена С НДС = add_vat(SparePart.price)
sum       = Decimal        # quantity × price, с НДС (зафиксировано)
price_without_vat = Decimal null  # снапшот SparePart.price (без НДС)
vat_rate  = Decimal null   # ставка на момент заказа (12)
```

### НДС

- `SparePart.price` в админке вводится **без НДС**. Дилер в каталоге, корзине и счёте видит цену **с НДС**: `models.add_vat(price)` = price × (100 + `VAT_RATE`) / 100, округлено до целого сума (`ROUND_HALF_UP`). Ставка — константа `VAT_RATE = 12` в `main/models.py`.
- `Invoice.total_amount`, `InvoiceItem.price/sum` — всегда с НДС (то, что дилер платит).
- Счёт на оплату (`invoice.html`) не меняется: те же колонки «Цена»/«Сумма», просто суммы уже с НДС. Разбивка «без НДС / в т.ч. НДС 12%» есть только в карточке заказа у сотрудников (`staff_order_detail`), и только у счетов, созданных после введения НДС.
- Миграция `0038_spare_part_vat` только добавляет поля, цены **не пересчитывает**. Старые цены (введённые с НДС) сотрудники перебивают вручную на цены без НДС. До этого к ним тоже прибавится 12%. Черновики, созданные до перехода, при подтверждении получат «изменилась цена» и пересчитаются.
- Проверка «цена изменилась» при подтверждении сравнивает и цену с НДС, и цену без НДС.

Если запчасть подорожает или переименуется — старый счёт продолжит показывать исходные значения. `part_id` остаётся (для аналитики — какая модель), но **не используется** при рендере счёта.

`on_delete=SET_NULL` — если запчасть удалят, FK обнулится, но имя/цена/сумма в `InvoiceItem` останутся.

---

## 9. Жизненный цикл заказа (статусы)

### 5 статусов

| Код | Лейбл | Цвет |
|-----|-------|------|
| `pending_payment` | Ожидание оплаты | 🟠 оранжевый |
| `paid` | Оплачено | 🟢 зелёный |
| `in_transit` | В пути | 🔵 синий |
| `delivered` | Доставлено | ⚫ серый |
| `cancelled` | Отменён | 🔴 красный |

### Матрица переходов

```python
ALLOWED_STATUS_TRANSITIONS = {
    'accountant': { 'pending_payment': ['paid', 'cancelled'],
                    'paid':            ['cancelled'] },
    'service':    { 'pending_payment': ['cancelled'],
                    'paid':            ['in_transit', 'cancelled'] },
    'dealer':     { 'pending_payment': ['cancelled'],
                    'in_transit':      ['delivered'] },
}
```

### Отмена заказа

- **Дилер** — свой заказ, пока он в «Ожидании оплаты»: кнопка «✕ Отменить заказ» в счёте → `POST /dealer/invoice/<id>/cancel-order/`.
- **Бухгалтер / сервис** — до отгрузки (`pending_payment` или `paid`): красная кнопка в карточке заказа → `POST /staff/orders/<id>/status/` со `status=cancelled`.
- После «В пути» отменить может только **админ** в админке.
- Причина отмены необязательна (спрашивается через prompt).

При отмене (`Invoice.set_cancelled`) все позиции **возвращаются на склад** (журнал: `order_cancel`), сохраняются `cancelled_at`, `cancelled_by`, `cancel_reason`. Номер счёта остаётся — дыр в нумерации нет. Из «Отменён» по матрице никуда не перейти.

**Админ может всё**: в админке статус меняется без матрицы ролей, но склад всё равно сходится — уход в «Отменён» возвращает остатки, возврат из «Отменён» списывает их заново (`Invoice.set_uncancelled`). Если остатков уже не хватает — форма (`InvoiceStatusForm`, и в карточке, и в `list_editable`) покажет ошибку и статус не сменится.

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
4. Документы:
   - **«📄 Счёт на оплату»** → полный счёт (тот же что у дилера, но без кнопки «Я получил», с навигацией «← К управлению заказом»)
   - **«📋 Спецификация»** → `/staff/orders/<id>/specification/` — спецификация к договору по образцу бумажной: «Спецификация №N к Договору № … от …», г. Ташкент + дата подтверждения, таблица (№, наименование, код детали, кол-во, цена без НДС, цена с НДС, общая с НДС), итого, подписи сторон. Номер спецификации = номер счёта. Дата договора — `DealerProfile.contract_date` (снапшот в `Invoice.buyer_contract_date`; если пусто — «от …» не печатается). Код детали — снапшот `InvoiceItem.part_number`, у старых позиций берётся из живой запчасти. У заказов до введения НДС цена без НДС = «—».

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
- ✅ `?next=` после логина проверяется `url_has_allowed_host_and_scheme` — ссылка вида `/dealer/login/?next=https://evil.com` не уведёт на чужой сайт (open redirect), вместо неё — свой кабинет роли

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
- Отмена черновика (`Invoice draft cancelled: id=N`)
- Отмена заказа (`Invoice cancelled: №N/Y by=<user> (<role>) reason=...`)
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
| `/dealer/invoice/<id>/cancel-order/` | POST | `dealer_invoice_cancel_order` | Отмена неоплаченного заказа + возврат на склад |
| `/dealer/invoices/` | GET | `dealer_invoices_list` | История счетов |

### Сотрудники

| URL | Кто | View | Что |
|-----|-----|------|-----|
| `/staff/orders/` | service+accountant | `staff_orders_list` | Все заказы |
| `/staff/orders/<id>/` | service+accountant | `staff_order_detail` | Управление статусом |
| `/staff/orders/<id>/status/` | POST | `staff_change_status` | Смена статуса (с ролью) |
| `/staff/orders/<id>/document/` | service+accountant | `staff_invoice_view` | Полный документ |
| `/staff/orders/<id>/specification/` | service+accountant | `staff_specification_view` | Спецификация к договору |
| `/staff/contracts/` | service | `staff_contracts` | Договоры дилеров |
| `/staff/contracts/<dealer_id>/new/` | service (POST) | `staff_contract_new` | Новый договор, нумерация с №1 |
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
parent_models      = M2M ParentModel (optional) — платформы/шасси, для фильтра
is_active          = Boolean
created_at, updated_at
```

### `SparePartType`

```python
name               = CharField (модельтрансляция: name_ru/uz/en, required ru)
created_at
```

Хитрый автокомплит в admin-форме: вводишь "Двигатель" → ищем `name_ru__iexact='двигатель'` → если есть, переиспользуем, если нет — создаём. В форме это текстовое поле `type_name` (FK `type` из формы исключён); тип ищется/создаётся только в `SparePartAdminForm.save()` — если форма или фото не прошли валидацию, лишний тип в БД не появится.

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
status                    = CharField(choices=5 values, default='pending_payment')

cancelled_at              = DateTime (NULL пока не отменён)
cancelled_by              = CharField  # username того, кто отменил
cancel_reason             = CharField

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

### `StockMovement`

```python
part            = FK SparePart (CASCADE)
delta           = Integer          # +N приход / −N расход
quantity_after  = PositiveInt      # остаток после изменения
reason          = CharField(choices: order / order_cancel / staff / admin)
invoice         = FK Invoice (SET_NULL, optional)
changed_by      = CharField        # username
comment         = CharField
created_at
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

### Цена изменилась между checkout и confirm

Админ поменял цену, пока дилер смотрел черновик. При confirm позиции черновика пересчитываются по новой цене, сумма обновляется, ответ 409 `{reload: true}` с перечнем изменившихся позиций. Страница перезагружается, дилер видит новую сумму и подтверждает снова. Склад и номер не тронуты, пока он не подтвердит.

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

Если нужно «откатить» заказ — его **отменяют** (статус «Отменён», см. раздел 9): позиции возвращаются на склад, документ и номер остаются в истории.

### Заказ 1 января ночью

`USE_TZ=True`, `timezone.now()` — в UTC. Заказ 1 января в 02:00 по Ташкенту — это ещё 31 декабря по UTC. Поэтому год берётся через `timezone.localdate().year` — счёт получит номер нового года.

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
| Модели магазина | [main/models.py](main/models.py) — `DealerProfile`, `SparePart`, `SparePartType`, `SparePartImage`, `Invoice`, `InvoiceItem`, `StockMovement` + `change_stock()` / `record_stock_change()` |
| Тесты | [main/tests/test_dealer_shop.py](main/tests/test_dealer_shop.py) — `python manage.py test main.tests.test_dealer_shop` |
| Утилиты форматирования | [main/utils/invoice_format.py](main/utils/invoice_format.py) — `format_uzs`, `format_date_ru`, `amount_in_words_uzs` |
| Валидаторы | [main/validators.py](main/validators.py) — `validate_image_size` |
| Очистка orphan-файлов | [main/signals_cleanup.py](main/signals_cleanup.py) |
| Views (магазин + staff + auth) | [main/views.py](main/views.py) |
| URL-карта | [main/urls.py](main/urls.py) |
| Формы | [main/forms.py](main/forms.py) — `DealerLoginForm`, `DealerProfileAdminForm`, `DealerPasswordChangeForm`, `SparePartAdminForm` |
| Админка | [main/admin.py](main/admin.py) — `DealerProfileAdmin`, `SparePartAdmin`, `SparePartTypeAdmin`, `InvoiceAdmin` (+ `InvoiceStatusForm`), `StockMovementAdmin` |
| Шаблоны дилера | `main/templates/main/dealer/`: `login.html`, `shop.html`, `shop_detail.html`, `cart.html`, `invoice.html`, `invoices_list.html`, `_profile_modal.html` |
| Шаблоны staff | `main/templates/main/dealer/`: `staff_orders.html`, `staff_order_detail.html`, `staff_parts.html` |
| JS-корзина | [main/static/js/dealer-cart.js](main/static/js/dealer-cart.js) |
