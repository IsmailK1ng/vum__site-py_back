"""
Тесты магазина запчастей: подтверждение заказа, отмена с возвратом на склад,
журнал склада, open redirect при логине, пагинация каталога, админ-форма запчасти.
"""
import json
from datetime import datetime
from decimal import Decimal
from unittest import mock
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core import signing
from django.test import TestCase, override_settings
from django.urls import reverse

from main import views
from main.forms import SparePartAdminForm
from main.models import (
    DealerProfile, Invoice, SparePart, SparePartType, StockMovement,
)


@override_settings(ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False)
class ShopTestBase(TestCase):
    PASSWORD = 'Vum-test-pass-2026'

    def setUp(self):
        self.ptype = SparePartType.objects.create(name='Фильтр', name_ru='Фильтр')
        self.part = SparePart.objects.create(
            part_number='F-001', name='Фильтр масляный', name_ru='Фильтр масляный',
            type=self.ptype, quantity=10, price=Decimal('100000'),
        )
        self.dealer = self.make_profile('dealer1', DealerProfile.ROLE_DEALER)
        self.service = self.make_profile('service1', DealerProfile.ROLE_SERVICE)
        self.accountant = self.make_profile('acc1', DealerProfile.ROLE_ACCOUNTANT)

    def make_profile(self, username, role):
        user = User.objects.create_user(username=username, password=self.PASSWORD)
        return DealerProfile.objects.create(
            user=user, role=role, name=username,
            company_name='ООО Тест', inn='123456789', contract_number='1/2026',
        )

    def login_as(self, profile):
        self.client.cookies[views.DEALER_COOKIE_NAME] = signing.dumps(
            {'pid': profile.id}, salt=views.DEALER_COOKIE_SALT,
        )

    def checkout(self, qty):
        resp = self.client.post(
            reverse('dealer_cart_checkout'),
            data=json.dumps({'items': [{'id': self.part.id, 'qty': qty}]}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        return Invoice.objects.get(id=resp.json()['invoice_id'])

    def confirmed_order(self, qty=3):
        self.login_as(self.dealer)
        invoice = self.checkout(qty)
        resp = self.client.post(reverse('dealer_invoice_confirm', args=[invoice.id]))
        self.assertEqual(resp.status_code, 200, resp.content)
        invoice.refresh_from_db()
        return invoice


class ConfirmTests(ShopTestBase):

    def test_confirm_writes_stock_movement(self):
        invoice = self.confirmed_order(qty=3)
        self.part.refresh_from_db()
        self.assertEqual(self.part.quantity, 7)
        move = StockMovement.objects.get(part=self.part)
        self.assertEqual((move.delta, move.quantity_after, move.reason), (-3, 7, StockMovement.REASON_ORDER))
        self.assertEqual(move.invoice, invoice)
        self.assertEqual(move.changed_by, 'dealer1')

    def test_confirm_uses_local_year(self):
        # 31.12.2026 21:00 UTC = 01.01.2027 02:00 по Ташкенту → счёт должен быть 2027 года
        fake_now = datetime(2026, 12, 31, 21, 0, tzinfo=ZoneInfo('UTC'))
        self.login_as(self.dealer)
        invoice = self.checkout(1)
        with mock.patch('django.utils.timezone.now', return_value=fake_now):
            self.client.post(reverse('dealer_invoice_confirm', args=[invoice.id]))
        invoice.refresh_from_db()
        self.assertEqual(invoice.year, 2027)

    def test_price_change_between_checkout_and_confirm(self):
        self.login_as(self.dealer)
        invoice = self.checkout(2)
        SparePart.objects.filter(id=self.part.id).update(price=Decimal('120000'))

        resp = self.client.post(reverse('dealer_invoice_confirm', args=[invoice.id]))
        self.assertEqual(resp.status_code, 409)
        self.assertTrue(resp.json()['reload'])

        invoice.refresh_from_db()
        self.assertIsNone(invoice.number)                       # всё ещё черновик
        # 120 000 без НДС → 134 400 с НДС, × 2 шт
        self.assertEqual(invoice.total_amount, Decimal('268800'))
        item = invoice.items.get()
        self.assertEqual((item.price, item.price_without_vat), (Decimal('134400'), Decimal('120000')))
        self.part.refresh_from_db()
        self.assertEqual(self.part.quantity, 10)                # склад не тронут

        # Повторное подтверждение уже по новой цене проходит
        resp = self.client.post(reverse('dealer_invoice_confirm', args=[invoice.id]))
        self.assertEqual(resp.status_code, 200)


class VatTests(ShopTestBase):
    """В админке цена без НДС, дилер везде видит и платит цену с НДС 12%."""

    def test_add_vat_rounds_to_sum(self):
        from main.models import add_vat
        self.assertEqual(add_vat(Decimal('331000')), Decimal('370720'))     # пример из спецификации
        self.assertEqual(add_vat(Decimal('100.05')), Decimal('112'))        # 112.056 → 112

    def test_checkout_snapshots_vat(self):
        self.login_as(self.dealer)
        invoice = self.checkout(2)
        item = invoice.items.get()
        self.assertEqual(item.price_without_vat, Decimal('100000'))
        self.assertEqual(item.vat_rate, Decimal('12'))
        self.assertEqual(item.price, Decimal('112000'))
        self.assertEqual(item.sum, Decimal('224000'))
        self.assertEqual(invoice.total_amount, Decimal('224000'))

    def test_shop_and_cart_api_show_price_with_vat(self):
        self.login_as(self.dealer)
        resp = self.client.get(reverse('dealer_shop'))
        self.assertContains(resp, '112 000 UZS')   # floatformat ставит неразрывный пробел
        resp = self.client.get(reverse('dealer_cart_api') + f'?ids={self.part.id}')
        self.assertEqual(resp.json()['items'][0]['price'], 112000.0)

    def test_invoice_document_unchanged_but_priced_with_vat(self):
        invoice = self.confirmed_order(qty=2)
        resp = self.client.get(reverse('dealer_invoice', args=[invoice.id]))
        self.assertNotContains(resp, 'НДС')                  # счёт на оплату — без разбивки
        self.assertContains(resp, '224 000,00')               # но суммы уже с НДС



class SpecificationTests(ShopTestBase):
    """Спецификация к договору: доступна сотрудникам, цены без/с НДС, код детали."""

    def test_staff_sees_specification(self):
        from datetime import date
        self.dealer.contract_date = date(2026, 8, 20)
        self.dealer.save()
        invoice = self.confirmed_order(qty=2)
        self.assertEqual(invoice.items.get().part_number, 'F-001')

        self.login_as(self.accountant)
        resp = self.client.get(reverse('staff_specification_view', args=[invoice.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f'СПЕЦИФИКАЦИЯ №{invoice.number}')
        self.assertContains(resp, 'к Договору № 1/2026 от 20.08.2026 г.')
        self.assertContains(resp, 'F-001')
        self.assertContains(resp, '100 000')      # цена без НДС
        self.assertContains(resp, '112 000')      # цена с НДС
        self.assertContains(resp, '224 000')      # общая
        self.assertNotContains(resp, ',00')       # без копеек

        detail = self.client.get(reverse('staff_order_detail', args=[invoice.id]))
        self.assertContains(detail, reverse('staff_specification_view', args=[invoice.id]))

    def test_dealer_cannot_open_specification(self):
        invoice = self.confirmed_order(qty=1)
        resp = self.client.get(reverse('staff_specification_view', args=[invoice.id]))
        self.assertEqual(resp.status_code, 302)

    def test_old_item_without_snapshots(self):
        invoice = self.confirmed_order(qty=1)
        invoice.items.update(part_number='', price_without_vat=None, vat_rate=None)
        self.login_as(self.service)
        resp = self.client.get(reverse('staff_specification_view', args=[invoice.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'F-001')        # код взят из живой запчасти
        self.assertContains(resp, '—')            # цены без НДС нет


class ContractNumberingTests(ShopTestBase):
    """Номер счёта/спецификации идёт внутри договора дилера; сервис может начать новый договор."""

    def test_numbering_per_dealer_contract(self):
        first = self.confirmed_order(qty=1)
        second = self.confirmed_order(qty=1)
        self.assertEqual((first.number, second.number), (1, 2))
        self.assertEqual(first.contract, second.contract)
        self.assertEqual(first.contract.number, '1/2026')

        other = self.make_profile('dealer2', DealerProfile.ROLE_DEALER)
        self.login_as(other)
        inv = self.checkout(1)
        self.client.post(reverse('dealer_invoice_confirm', args=[inv.id]))
        inv.refresh_from_db()
        self.assertEqual(inv.number, 1)                 # у другого дилера своя нумерация

    def test_service_starts_new_contract(self):
        old = self.confirmed_order(qty=1)
        self.confirmed_order(qty=1)

        self.login_as(self.service)
        page = self.client.get(reverse('staff_contracts'))
        self.assertContains(page, '№ 1/2026')
        resp = self.client.post(
            reverse('staff_contract_new', args=[self.dealer.id]),
            {'contract_number': 'AVN-24', 'contract_date': '2026-11-20'},
        )
        self.assertEqual(resp.status_code, 302)
        self.dealer.refresh_from_db()
        self.assertEqual(self.dealer.contract_number, 'AVN-24')

        new = self.confirmed_order(qty=1)
        self.assertEqual(new.number, 1)
        self.assertEqual(new.buyer_contract_number, 'AVN-24')
        self.assertEqual(str(new.buyer_contract_date), '2026-11-20')
        old.refresh_from_db()
        self.assertEqual((old.number, old.buyer_contract_number), (1, '1/2026'))   # старое не тронуто

        self.login_as(self.service)
        spec = self.client.get(reverse('staff_specification_view', args=[new.id]))
        self.assertContains(spec, 'СПЕЦИФИКАЦИЯ №1')
        self.assertContains(spec, 'к Договору № AVN-24 от 20.11.2026 г.')

    def test_new_contract_requires_number_and_date(self):
        self.login_as(self.service)
        self.client.post(reverse('staff_contract_new', args=[self.dealer.id]),
                         {'contract_number': 'AVN-24', 'contract_date': ''})
        self.assertFalse(self.dealer.contracts.exists())

    def test_only_service_manages_contracts(self):
        for who in (self.accountant, self.dealer):
            self.login_as(who)
            self.assertEqual(self.client.get(reverse('staff_contracts')).status_code, 302)
            self.client.post(reverse('staff_contract_new', args=[self.dealer.id]),
                             {'contract_number': 'X', 'contract_date': '2026-11-20'})
        self.assertFalse(self.dealer.contracts.exists())

    def test_draft_confirmed_after_new_contract_gets_new_requisites(self):
        self.login_as(self.dealer)
        draft = self.checkout(1)
        self.login_as(self.service)
        self.client.post(reverse('staff_contract_new', args=[self.dealer.id]),
                         {'contract_number': 'AVN-25', 'contract_date': '2026-12-01'})
        self.login_as(self.dealer)
        self.client.post(reverse('dealer_invoice_confirm', args=[draft.id]))
        draft.refresh_from_db()
        self.assertEqual((draft.number, draft.buyer_contract_number), (1, 'AVN-25'))

class CancelTests(ShopTestBase):

    def test_dealer_cancels_unpaid_order(self):
        invoice = self.confirmed_order(qty=4)
        resp = self.client.post(
            reverse('dealer_invoice_cancel_order', args=[invoice.id]), {'reason': 'Передумал'},
        )
        self.assertEqual(resp.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.STATUS_CANCELLED)
        self.assertEqual(invoice.cancel_reason, 'Передумал')
        self.assertEqual(invoice.cancelled_by, 'dealer1')
        self.assertEqual(invoice.number, 1)                     # номер сохраняется
        self.part.refresh_from_db()
        self.assertEqual(self.part.quantity, 10)
        self.assertTrue(StockMovement.objects.filter(
            invoice=invoice, reason=StockMovement.REASON_ORDER_CANCEL, delta=4,
        ).exists())

    def test_dealer_cannot_cancel_paid_order(self):
        invoice = self.confirmed_order()
        Invoice.objects.filter(id=invoice.id).update(status=Invoice.STATUS_PAID)
        resp = self.client.post(reverse('dealer_invoice_cancel_order', args=[invoice.id]))
        self.assertEqual(resp.status_code, 404)
        self.part.refresh_from_db()
        self.assertEqual(self.part.quantity, 7)

    def test_dealer_cannot_cancel_foreign_order(self):
        invoice = self.confirmed_order()
        other = self.make_profile('dealer2', DealerProfile.ROLE_DEALER)
        self.login_as(other)
        resp = self.client.post(reverse('dealer_invoice_cancel_order', args=[invoice.id]))
        self.assertEqual(resp.status_code, 404)

    def test_accountant_cancels_paid_order(self):
        invoice = self.confirmed_order(qty=2)
        Invoice.objects.filter(id=invoice.id).update(status=Invoice.STATUS_PAID)
        self.login_as(self.accountant)
        resp = self.client.post(
            reverse('staff_change_status', args=[invoice.id]),
            {'status': Invoice.STATUS_CANCELLED, 'reason': 'Возврат денег'},
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.part.refresh_from_db()
        self.assertEqual(self.part.quantity, 10)

    def test_service_cannot_cancel_in_transit(self):
        invoice = self.confirmed_order()
        Invoice.objects.filter(id=invoice.id).update(status=Invoice.STATUS_IN_TRANSIT)
        self.login_as(self.service)
        resp = self.client.post(
            reverse('staff_change_status', args=[invoice.id]), {'status': Invoice.STATUS_CANCELLED},
        )
        self.assertEqual(resp.status_code, 403)

    def test_cancelled_order_cannot_move_further(self):
        invoice = self.confirmed_order()
        self.client.post(reverse('dealer_invoice_cancel_order', args=[invoice.id]))
        self.login_as(self.accountant)
        resp = self.client.post(
            reverse('staff_change_status', args=[invoice.id]), {'status': Invoice.STATUS_PAID},
        )
        self.assertEqual(resp.status_code, 403)


@override_settings(ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False)
class AdminInvoiceTests(ShopTestBase):

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser('admin', 'a@a.a', self.PASSWORD)

    def admin_set_status(self, invoice, status):
        self.client.force_login(self.admin)
        return self.client.post(
            reverse('admin:main_invoice_change', args=[invoice.id]),
            {
                'status': status,
                'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '1',
                'items-MIN_NUM_FORMS': '0', 'items-MAX_NUM_FORMS': '1000',
                'items-0-id': str(invoice.items.get().id), 'items-0-invoice': str(invoice.id),
            },
        )

    def test_admin_cancel_and_uncancel_moves_stock(self):
        invoice = self.confirmed_order(qty=3)
        resp = self.admin_set_status(invoice, Invoice.STATUS_CANCELLED)
        self.assertEqual(resp.status_code, 302, resp.content[:2000])
        self.part.refresh_from_db()
        self.assertEqual(self.part.quantity, 10)

        resp = self.admin_set_status(invoice, Invoice.STATUS_PAID)
        self.assertEqual(resp.status_code, 302)
        self.part.refresh_from_db()
        self.assertEqual(self.part.quantity, 7)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.STATUS_PAID)
        self.assertEqual(invoice.cancelled_by, '')

    def test_admin_uncancel_blocked_when_stock_short(self):
        invoice = self.confirmed_order(qty=3)
        self.admin_set_status(invoice, Invoice.STATUS_CANCELLED)
        SparePart.objects.filter(id=self.part.id).update(quantity=1)

        resp = self.admin_set_status(invoice, Invoice.STATUS_PAID)
        self.assertEqual(resp.status_code, 200)                 # форма с ошибкой
        self.assertContains(resp, 'не хватает на складе')
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.STATUS_CANCELLED)

    def test_admin_sparepart_add_page(self):
        self.client.force_login(self.admin)
        url = reverse('admin:main_sparepart_add')
        self.assertContains(self.client.get(url), 'name="type_name"')
        resp = self.client.post(url, {
            'part_number': 'ADM-1', 'is_active': 'on', 'type_name': 'Тормоза',
            'name_ru': 'Колодка', 'quantity': '5', 'price': '50000',
            'images-TOTAL_FORMS': '0', 'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0', 'images-MAX_NUM_FORMS': '1000',
            'stock_movements-TOTAL_FORMS': '0', 'stock_movements-INITIAL_FORMS': '0',
            'stock_movements-MIN_NUM_FORMS': '0', 'stock_movements-MAX_NUM_FORMS': '0',
        })
        self.assertEqual(resp.status_code, 302, resp.content[:3000])
        part = SparePart.objects.get(part_number='ADM-1')
        self.assertEqual(part.type.name_ru, 'Тормоза')
        move = StockMovement.objects.get(part=part)
        self.assertEqual((move.delta, move.quantity_after), (5, 5))
        self.assertEqual(self.client.get(reverse('admin:main_sparepart_change', args=[part.id])).status_code, 200)

    def test_admin_quantity_edit_is_logged(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('admin:main_sparepart_changelist'), {
            'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
            'form-0-id': str(self.part.id),
            'form-0-quantity': '25', 'form-0-price': '100000', 'form-0-is_active': 'on',
            '_save': 'Сохранить',
        })
        self.assertEqual(resp.status_code, 302)
        move = StockMovement.objects.get(part=self.part)
        self.assertEqual((move.delta, move.quantity_after, move.reason), (15, 25, StockMovement.REASON_ADMIN))


class PagesRenderTests(ShopTestBase):

    def test_pages_render_for_cancelled_order(self):
        invoice = self.confirmed_order()
        resp = self.client.get(reverse('dealer_invoice', args=[invoice.id]))
        self.assertContains(resp, 'id="invoice-cancel-order-btn"')
        self.assertContains(resp, f'data-owner="{self.dealer.id}"')

        self.client.post(reverse('dealer_invoice_cancel_order', args=[invoice.id]), {'reason': 'Тест'})
        for name in ('dealer_shop', 'dealer_cart', 'dealer_invoices_list'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        resp = self.client.get(reverse('dealer_invoice', args=[invoice.id]))
        self.assertContains(resp, 'Заказ отменён')
        self.assertNotContains(resp, 'id="invoice-cancel-order-btn"')

        self.login_as(self.service)
        resp = self.client.get(reverse('staff_order_detail', args=[invoice.id]))
        self.assertContains(resp, 'Причина: Тест')
        for url in (reverse('staff_orders_list'), reverse('staff_invoice_view', args=[invoice.id]),
                    reverse('staff_parts_list')):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_staff_sees_cancel_button(self):
        invoice = self.confirmed_order()
        self.login_as(self.accountant)
        resp = self.client.get(reverse('staff_order_detail', args=[invoice.id]))
        self.assertContains(resp, 'data-new-status="cancelled"')
        self.assertContains(resp, 'data-new-status="paid"')


class StaffStockTests(ShopTestBase):

    def test_staff_quantity_update_is_logged(self):
        self.login_as(self.service)
        resp = self.client.post(
            reverse('staff_part_update_quantity', args=[self.part.id]),
            data=json.dumps({'delta': -4}), content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        move = StockMovement.objects.get(part=self.part)
        self.assertEqual((move.delta, move.quantity_after, move.reason), (-4, 6, StockMovement.REASON_STAFF))


class LoginRedirectTests(ShopTestBase):

    def login(self, next_url):
        return self.client.post(
            reverse('dealer_login') + '?next=' + next_url,
            {'username': 'dealer1', 'password': self.PASSWORD},
        )

    def test_external_next_ignored(self):
        resp = self.login('https://evil.com/phish')
        self.assertEqual(resp.url, reverse('dealer_shop'))

    def test_protocol_relative_next_ignored(self):
        resp = self.login('//evil.com')
        self.assertEqual(resp.url, reverse('dealer_shop'))

    def test_internal_next_kept(self):
        resp = self.login('/dealer/cart/')
        self.assertEqual(resp.url, '/dealer/cart/')


class CatalogTests(ShopTestBase):

    def test_pagination_keeps_filters(self):
        for i in range(30):
            SparePart.objects.create(
                part_number=f'P-{i:03}', name=f'Деталь {i}', name_ru=f'Деталь {i}',
                type=self.ptype, quantity=1, price=Decimal('1000'),
            )
        self.login_as(self.dealer)
        resp = self.client.get(reverse('dealer_shop'), {'type': self.ptype.id, 'page': 2})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['page_obj'].number, 2)
        self.assertEqual(len(resp.context['parts']), 31 - views.SHOP_PAGE_SIZE)
        self.assertContains(resp, f'type={self.ptype.id}&amp;page=1')

    def test_service_sees_part_without_cart(self):
        self.login_as(self.service)
        resp = self.client.get(reverse('dealer_part_detail', args=[self.part.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'id="add-to-cart-btn"')
        self.assertNotContains(resp, 'dealer-cart.js')


class SparePartFormTests(ShopTestBase):

    def test_invalid_form_does_not_create_type(self):
        form = SparePartAdminForm(data={
            'part_number': self.part.part_number,      # дубль артикула → форма невалидна
            'type_name': 'Совсем новый тип',
            'name_ru': 'X', 'quantity': 1, 'price': '1',
        })
        self.assertFalse(form.is_valid())
        self.assertFalse(SparePartType.objects.filter(name_ru='Совсем новый тип').exists())

    def test_existing_type_reused_case_insensitive(self):
        form = SparePartAdminForm(data={
            'part_number': 'NEW-1', 'type_name': '  фильтр ',
            'name_ru': 'Новый', 'quantity': 1, 'price': '1',
        })
        self.assertTrue(form.is_valid(), form.errors)
        part = form.save()
        self.assertEqual(part.type, self.ptype)
        self.assertEqual(SparePartType.objects.count(), 1)


class JavaImportTests(ShopTestBase):
    """Импорт запчастей из SpareParts.java в админке."""

    JAVA = '''
        public record SparePart(int no, String partNumber, String name) {}
        List.of(
            new SparePart(1, "NEW-001", "Новая деталь"),
            new SparePart(2, "F-001", "Фильтр масляный новый"),
            new SparePart(3, "NEW-001", "Повтор"),
            new SparePart(4, "NEW-002", "Старый формат", "Old format"),
            new SparePart(5, "NEW-003", ""),
            new SparePart(6, "NEW-004", "Пружина типа \\"Втулка-лист\\"")
        );
    '''

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser('admin', 'a@a.a', self.PASSWORD)
        self.client.force_login(self.admin)
        self.url = reverse('admin:main_sparepart_import_java')

    def upload(self, text, **extra):
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile('SpareParts.java', text.encode('utf-8'), content_type='text/plain')
        return self.client.post(self.url, {'java_file': f, 'type_name': 'Импорт', **extra})

    def test_parser_handles_both_formats(self):
        from main.utils.java_parts import parse_java_parts
        self.assertEqual(parse_java_parts(self.JAVA), [
            ('NEW-001', 'Новая деталь'), ('F-001', 'Фильтр масляный новый'), ('NEW-001', 'Повтор'),
            ('NEW-002', 'Старый формат'), ('NEW-003', ''), ('NEW-004', 'Пружина типа "Втулка-лист"'),
        ])

    def test_changelist_has_button(self):
        resp = self.client.get(reverse('admin:main_sparepart_changelist'))
        self.assertContains(resp, self.url)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_import_creates_inactive_parts_and_keeps_existing(self):
        resp = self.upload(self.JAVA)
        self.assertEqual(resp.status_code, 200)
        new = SparePart.objects.get(part_number='NEW-001')
        self.assertEqual((new.name_ru, new.price, new.quantity, new.is_active, new.type.name_ru),
                         ('Новая деталь', 0, 0, False, 'Импорт'))
        self.assertTrue(SparePart.objects.filter(part_number='NEW-002', name_ru='Старый формат').exists())
        self.assertEqual(SparePart.objects.get(part_number='NEW-004').name_ru, 'Пружина типа "Втулка-лист"')
        self.assertFalse(SparePart.objects.filter(part_number='NEW-003').exists())    # пустое имя
        self.part.refresh_from_db()
        self.assertEqual((self.part.name_ru, self.part.price, self.part.is_active),
                         ('Фильтр масляный', Decimal('100000'), True))                  # существующая не тронута
        result = resp.context['result']
        self.assertEqual((len(result['created']), len(result['skipped']), result['duplicates'], result['no_name']),
                         (3, 1, ['NEW-001'], ['NEW-003']))

        # Повторный импорт ничего не дублирует
        self.upload(self.JAVA)
        self.assertEqual(SparePart.objects.filter(part_number__startswith='NEW-').count(), 3)

    def test_update_names_option(self):
        self.upload(self.JAVA, update_names='1')
        self.part.refresh_from_db()
        self.assertEqual((self.part.name_ru, self.part.price), ('Фильтр масляный новый', Decimal('100000')))

    def test_bad_file(self):
        resp = self.upload('class Nothing {}')
        self.assertContains(resp, 'не найдено ни одной строки')
        self.assertEqual(SparePart.objects.count(), 1)

    def test_real_java_file(self):
        from pathlib import Path
        from django.conf import settings
        from main.utils.java_parts import parse_java_parts
        path = Path(settings.BASE_DIR) / 'data' / 'SpareParts.java'
        if not path.exists():   # data/ в .gitignore — на других машинах файла нет
            self.skipTest('data/SpareParts.java отсутствует')
        text = path.read_text(encoding='utf-8')
        parsed = parse_java_parts(text)
        self.assertEqual(len(parsed), 868)
        self.assertTrue(all(name for _, name in parsed))
        resp = self.upload(text)
        self.assertEqual(SparePart.objects.count() - 1, len(resp.context['result']['created']))
