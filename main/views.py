# main/views.py

# ========== СТАНДАРТНАЯ БИБЛИОТЕКА ==========
import json
import logging
from datetime import datetime, timedelta
from functools import wraps

# ========== DJANGO CORE ==========
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from django.core import signing
from django.core.paginator import Paginator
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Count, Q, Avg, F
from django.db.models.functions import TruncHour, TruncDate
from django.http import HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import translation, timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

# ========== DJANGO REST FRAMEWORK ==========
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from main.utils.recaptcha import verify_recaptcha, get_client_ip
# ========== ЛОКАЛЬНЫЕ ИМПОРТЫ ==========
from .models import (
    News,
    ContactForm,
    JobApplication,
    Vacancy,
    Product,
    Dealer,
    DealerService,
    BecomeADealerPage,
    BecomeADealerApplication,
    Promotion,
    FAQItem,
    REGION_CHOICES,
    TeamDepartment,
    TeamMember,
    DealerProfile,
    SparePart, SparePartType, ParentModel,
    Invoice, InvoiceItem,
    StockMovement, change_stock, record_stock_change, VAT_RATE,
    DealerContract, current_contract,
)
from django.db import transaction, IntegrityError
from decimal import Decimal
from main.utils.invoice_format import (
    format_uzs, format_date_ru, amount_in_words_uzs,
    _RU_MONTHS as MONTHS_RU_GENITIVE,
)
from .forms import DealerLoginForm, DealerPasswordChangeForm
from .serializers import (
    NewsSerializer, 
    ContactFormSerializer, 
    JobApplicationSerializer, 
    ProductCardSerializer, 
    ProductDetailSerializer,
    DealerSerializer, 
    DealerServiceSerializer, 
    BecomeADealerPageSerializer, 
    BecomeADealerApplicationSerializer,
    PromotionSerializer,
    VacancySerializer
)

# ========== LOGGER ==========
logger = logging.getLogger('django')

# === FRONTEND views === 

def index(request):
    """Главная страница с динамическим слайдером"""
    try:
        from django.utils.translation import get_language
        current_lang = get_language()
        
        news_list = News.objects.filter(
            is_active=True
        ).select_related('author').order_by('-order', '-created_at')[:8]
        
        featured_products = Product.objects.filter(
            is_active=True,
            is_featured=True
        ).order_by('-slider_order', '-created_at')[:10]
        
        slider_data = []
        for product in featured_products:
            title = getattr(product, f'title_{current_lang}', None) or product.title
            price = getattr(product, f'slider_price_{current_lang}', None) or product.slider_price or 'Narx so\'rang'
            price_old = getattr(product, f'slider_price_old_{current_lang}', None) or product.slider_price_old or ''
            power = getattr(product, f'slider_power_{current_lang}', None) or product.slider_power or '—'
            fuel = getattr(product, f'slider_fuel_consumption_{current_lang}', None) or product.slider_fuel_consumption or '—'

            slider_item = {
                'year': product.slider_year,
                'title': title,
                'price': price,
                # Пустая строка = акции нет, в слайдере просто не будет зачёркнутой цены
                'price_old': price_old,
                'power': power,
                'mpg': fuel,
                'image': None,
                'link': f'/products/{product.slug}/',
            }
            
            if product.slider_image:
                slider_item['image'] = product.slider_image.url
            elif product.main_image:
                slider_item['image'] = product.main_image.url
            
            slider_data.append(slider_item)
        
        context = {
            'news_list': news_list,
            'slider_products': json.dumps(slider_data, ensure_ascii=False),
            'featured_count': len(slider_data),
        }
        
        return render(request, 'main/index.html', context)
    
    except Exception as e:
        logger.error(f"Ошибка на главной странице: {str(e)}", exc_info=True)
        return render(request, 'main/index.html', {'slider_products': '[]', 'news_list': []})


def about(request):
    members = (
        TeamMember.objects
        .filter(is_active=True)
        .order_by('order')[:12]
    )
    return render(request, 'main/about.html', {'members': members})


def contact(request):
    return render(request, 'main/contact.html')


def services(request):
    return render(request, 'main/services.html')


def faq(request):
    faq_items = FAQItem.objects.filter(is_active=True).order_by('order')
    return render(request, 'main/faq.html', {'faq_items': faq_items})


def team(request):
    members = (
        TeamMember.objects
        .filter(is_active=True)
        .prefetch_related('links')
        .order_by('order')
    )
    return render(request, 'main/team.html', {'members': members})


# ========== ДИЛЕРСКАЯ АВТОРИЗАЦИЯ (ОТДЕЛЬНЫЙ COOKIE) ==========
# Сознательно НЕ используем Django session/auth_login — иначе дилер и
# админ делили бы один cookie `sessionid` и затирали друг друга.
# Здесь свой подписанный cookie 'dealer_sid' — параллельно с админской сессией.

DEALER_COOKIE_NAME    = 'dealer_sid'
DEALER_COOKIE_MAX_AGE = 60 * 60 * 8  # 8 часов
DEALER_COOKIE_SALT    = 'main.dealer-auth.v1'


def _set_dealer_cookie(response, profile_id):
    signed = signing.dumps({'pid': profile_id}, salt=DEALER_COOKIE_SALT)
    response.set_cookie(
        DEALER_COOKIE_NAME,
        signed,
        max_age=DEALER_COOKIE_MAX_AGE,
        httponly=True,           # JS не достанет — защита от XSS
        samesite='Lax',          # cross-site post-запросы не присылают cookie
        secure=not settings.DEBUG,
    )


def _clear_dealer_cookie(response):
    response.delete_cookie(DEALER_COOKIE_NAME)


def _get_dealer_profile_from_request(request):
    """Читает cookie, проверяет подпись, возвращает активный DealerProfile или None."""
    raw = request.COOKIES.get(DEALER_COOKIE_NAME)
    if not raw:
        return None
    try:
        data = signing.loads(raw, salt=DEALER_COOKIE_SALT, max_age=DEALER_COOKIE_MAX_AGE)
    except signing.BadSignature:
        # подделка или испорченный cookie
        return None
    profile_id = data.get('pid')
    if not profile_id:
        return None
    profile = (
        DealerProfile.objects
        .filter(id=profile_id, is_active=True)
        .select_related('user')
        .first()
    )
    if profile and profile.user.is_active:
        return profile
    return None


def _role_required(role_check, view_func):
    """Общий конструктор декоратора, проверяющий cookie + роль.

    role_check(profile) → bool: True если роль подходит.
    Не подошла роль → редирект в кабинет той роли которая ему доступна
    (а не logout — чтоб сотрудник случайно зайдя на /dealer/ не вылетал).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile = _get_dealer_profile_from_request(request)
        if not profile:
            response = redirect('dealer_login')
            _clear_dealer_cookie(response)
            return response
        if not role_check(profile):
            return redirect(_landing_url_for(profile))
        request.dealer_profile = profile
        return view_func(request, *args, **kwargs)
    return wrapper


def _landing_url_for(profile):
    """Куда вести пользователя сразу после логина / при попытке открыть чужой раздел."""
    if profile.is_dealer:
        return reverse('dealer_shop')
    # Сервис и бухгалтер — оба на список заказов
    return reverse('staff_orders_list')


def dealer_required(view_func):
    """Только для роли 'dealer' (покупатель). Чужие роли → их собственная landing."""
    return _role_required(lambda p: p.is_dealer, view_func)


def staff_required(view_func):
    """Сервис ИЛИ бухгалтер."""
    return _role_required(lambda p: p.is_staff_user, view_func)


def service_required(view_func):
    """Только сервис (раздел склада, изменения остатков)."""
    return _role_required(lambda p: p.is_service, view_func)


def accountant_required(view_func):
    """Только бухгалтер."""
    return _role_required(lambda p: p.is_accountant, view_func)


def dealer_or_service_required(view_func):
    """Дилер (покупатель) ИЛИ сервис — карточка запчасти нужна обоим:
    дилеру для покупки, сервису — сверить отображение фото/описания."""
    return _role_required(lambda p: p.is_dealer or p.is_service, view_func)


@sensitive_post_parameters('password')
@never_cache
@require_http_methods(['GET', 'POST'])
def dealer_login(request):
    """Страница входа для дилеров.
    - При уже валидном dealer_sid cookie — редирект в магазин.
    - На ошибке отдаём одинаковое сообщение (без намёков что именно неверно).
    - authenticate() сверяет пароль через User-таблицу, но Django session НЕ создаётся.
    """
    existing_profile = _get_dealer_profile_from_request(request)
    if existing_profile:
        return redirect(_landing_url_for(existing_profile))

    form = DealerLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Неверный логин или пароль.')
            logger.warning(
                'Dealer login failed: username=%s ip=%s ua=%s',
                username,
                request.META.get('REMOTE_ADDR'),
                request.META.get('HTTP_USER_AGENT', '')[:200],
            )
        else:
            profile = DealerProfile.objects.filter(user=user, is_active=True).first()
            if not profile or not user.is_active:
                messages.error(request, 'Учётная запись неактивна или не является дилерской.')
                logger.warning('Dealer login blocked (no/inactive profile): username=%s', username)
            else:
                logger.info('Dealer login: username=%s ip=%s', username, request.META.get('REMOTE_ADDR'))
                # Куда уводим зависит от роли. ?next= уважаем только если он ведёт
                # на наш же сайт — иначе ссылка /dealer/login/?next=https://evil.com
                # после входа увела бы дилера на чужой сайт (open redirect).
                next_url = request.GET.get('next') or ''
                if not url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    next_url = _landing_url_for(profile)
                response = redirect(next_url)
                _set_dealer_cookie(response, profile.id)
                return response

    return render(request, 'main/dealer/login.html', {'form': form})


@require_http_methods(['POST', 'GET'])
def dealer_logout(request):
    profile = _get_dealer_profile_from_request(request)
    if profile:
        logger.info('Dealer logout: username=%s', profile.user.username)
    response = redirect('dealer_login')
    _clear_dealer_cookie(response)
    return response


SHOP_PAGE_SIZE = 24  # кратно 2/3/4 колонкам сетки каталога


@never_cache
@dealer_required
def dealer_shop(request):
    """Магазин запчастей дилера (главный экран кабинета).
    Auth через signed cookie 'dealer_sid' — НЕ через Django session.
    """
    profile = request.dealer_profile

    # Параметры фильтрации
    q          = (request.GET.get('q') or '').strip()
    parent_id  = (request.GET.get('parent') or '').strip()
    type_id    = (request.GET.get('type') or '').strip()

    parts = (
        SparePart.objects
        .filter(is_active=True)
        .select_related('type')
        .prefetch_related('images', 'parent_models')
    )

    # Поиск по артикулу ИЛИ названию (RU и base). icontains — case-insensitive.
    if q:
        parts = parts.filter(
            Q(part_number__icontains=q)
            | Q(name__icontains=q)
            | Q(name_ru__icontains=q)
        )

    # Фильтры по селектам — только если значение валидное число.
    # parent_models — M2M, фильтр по одному id может задвоить строки join'ом.
    if parent_id.isdigit():
        parts = parts.filter(parent_models__id=int(parent_id)).distinct()
    if type_id.isdigit():
        parts = parts.filter(type_id=int(type_id))

    parts = parts.order_by('-updated_at')
    page_obj = Paginator(parts, SHOP_PAGE_SIZE).get_page(request.GET.get('page'))

    # Текущие фильтры без page — для ссылок пагинации
    filter_params = request.GET.copy()
    filter_params.pop('page', None)

    # Списки для селектов в фильтр-баре — только сущности, у которых есть запчасти
    parents_with_parts = (
        ParentModel.objects
        .filter(spare_parts__is_active=True)
        .distinct()
        .order_by('name')
    )
    types_with_parts = (
        SparePartType.objects
        .filter(parts__is_active=True)
        .distinct()
        .order_by('name')
    )

    return render(request, 'main/dealer/shop.html', {
        'profile': profile,
        'parts': page_obj.object_list,
        'page_obj': page_obj,
        'filter_query': filter_params.urlencode(),
        'parents_with_parts': parents_with_parts,
        'types_with_parts': types_with_parts,
        'selected_parent': parent_id,
        'selected_type': type_id,
        'search_query': q,
    })


@never_cache
@dealer_or_service_required
def dealer_part_detail(request, part_id):
    """Карточка конкретной запчасти + рекомендации.
    Приоритет рекомендаций: тот же тип ИЛИ та же родительская модель (без дублей).
    Если таких нет — fallback на 4 свежих активных запчасти.
    """
    profile = request.dealer_profile

    part = (
        SparePart.objects
        .select_related('type')
        .prefetch_related('images', 'parent_models')
        .filter(is_active=True)
        .filter(pk=part_id)
        .first()
    )
    if not part:
        messages.warning(request, 'Запчасть не найдена или снята с продажи.')
        return redirect('dealer_shop')

    # Рекомендации: тот же тип ИЛИ хотя бы одна общая родительская модель
    rec_qs = (
        SparePart.objects
        .filter(is_active=True)
        .exclude(pk=part.pk)
        .select_related('type')
        .prefetch_related('images', 'parent_models')
    )
    rec_filter = Q(type=part.type)
    parent_ids = list(part.parent_models.values_list('id', flat=True))
    if parent_ids:
        rec_filter |= Q(parent_models__id__in=parent_ids)
    recommendations = list(rec_qs.filter(rec_filter).distinct().order_by('-updated_at')[:4])

    # Fallback — берём свежие активные запчасти если по типу/модели ничего
    if not recommendations:
        recommendations = list(rec_qs.order_by('-updated_at')[:4])

    return render(request, 'main/dealer/shop_detail.html', {
        'profile': profile,
        'part': part,
        'recommendations': recommendations,
    })


@never_cache
@dealer_required
def dealer_cart_view(request):
    """Страница корзины. Содержимое тащим из localStorage клиента — здесь только shell."""
    return render(request, 'main/dealer/cart.html', {'profile': request.dealer_profile})


@sensitive_post_parameters('current_password', 'new_password', 'new_password_confirm')
@dealer_required
@require_http_methods(['POST'])
def dealer_change_password(request):
    """JSON-endpoint смены пароля из модалки кабинета.
    Текущий пароль обязателен. После смены сессия дилера (cookie dealer_sid) НЕ
    инвалидируется — нет смысла, в нём нет user_id, только profile_id.
    """
    profile = request.dealer_profile
    form = DealerPasswordChangeForm(request.POST, user=profile.user)
    if not form.is_valid():
        # Возвращаем ошибки в формате {field: [messages]}
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)

    profile.user.set_password(form.cleaned_data['new_password'])
    profile.user.save(update_fields=['password'])
    logger.info('Dealer password changed: username=%s', profile.user.username)
    return JsonResponse({'ok': True})


@dealer_required
@require_http_methods(['GET'])
def dealer_cart_api(request):
    """Возвращает данные по запчастям из ?ids=1,2,3 — для рендера корзины на клиенте.
    Только активные запчасти. Если ID нет в БД — клиент молча отбросит.
    """
    raw = (request.GET.get('ids') or '').strip()
    ids = []
    for token in raw.split(','):
        token = token.strip()
        if token.isdigit():
            ids.append(int(token))
    ids = ids[:100]  # защита от слишком больших запросов

    if not ids:
        return JsonResponse({'items': []})

    parts = (
        SparePart.objects
        .filter(id__in=ids, is_active=True)
        .select_related('type')
        .prefetch_related('images')
    )
    items = []
    for p in parts:
        first_image = p.images.first()
        items.append({
            'id': p.id,
            'part_number': p.part_number,
            'name': p.name_ru or p.name,
            'type': (p.type.name_ru or p.type.name) if p.type_id else None,
            'price': float(p.price_with_vat),   # дилер видит цену с НДС
            'price_without_vat': float(p.price),
            'quantity_available': p.quantity,
            'image_url': first_image.image.url if first_image else None,
        })
    return JsonResponse({'items': items})


@never_cache
@dealer_required
@require_http_methods(['POST'])
def dealer_cart_checkout(request):
    """Создание ЧЕРНОВИКА счёта из корзины.

    Принимает JSON: {"items": [{"id": <part_id>, "qty": <int>}, ...]}.
    Создаёт Invoice БЕЗ номера/года (черновик) + InvoiceItem.
    Склад НЕ списываем — это делается в confirm.
    Прежние черновики этого дилера удаляются (1 черновик за раз).
    """
    profile = request.dealer_profile

    if not profile.company_name or not profile.inn or not profile.contract_number:
        return JsonResponse({
            'ok': False,
            'error': 'Реквизиты компании не заполнены. Свяжитесь с администратором.',
        }, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        raw_items = payload.get('items') or []
        assert isinstance(raw_items, list)
    except (json.JSONDecodeError, AssertionError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Некорректный формат данных'}, status=400)

    if not raw_items:
        return JsonResponse({'ok': False, 'error': 'Корзина пуста'}, status=400)

    requested = {}
    for it in raw_items:
        try:
            pid = int(it['id'])
            qty = int(it['qty'])
        except (TypeError, ValueError, KeyError):
            continue
        if pid > 0 and qty > 0:
            requested[pid] = requested.get(pid, 0) + qty

    if not requested:
        return JsonResponse({'ok': False, 'error': 'Не указаны корректные позиции'}, status=400)

    parts_by_id = {
        p.id: p
        for p in SparePart.objects.filter(id__in=requested.keys(), is_active=True)
    }
    if not parts_by_id:
        return JsonResponse({'ok': False, 'error': 'Ни одна позиция недоступна'}, status=400)

    try:
        with transaction.atomic():
            # Чистим старые черновики этого дилера — пусть будет максимум один
            Invoice.objects.filter(dealer=profile, number__isnull=True).delete()

            # Создаём пустой черновик (без year/number — присвоятся при подтверждении)
            invoice = Invoice.objects.create(
                dealer=profile,
                year=None,
                number=None,
                buyer_company_name=profile.company_name,
                buyer_inn=profile.inn,
                buyer_contract_number=profile.contract_number,
                buyer_contract_date=profile.contract_date,
                total_amount=Decimal('0'),
            )

            total = Decimal('0')
            for pid, qty in requested.items():
                part = parts_by_id.get(pid)
                if not part:
                    continue
                actual_qty = min(qty, part.quantity)
                if actual_qty < 1:
                    continue
                price = part.price_with_vat
                line_sum = (price * actual_qty).quantize(Decimal('0.01'))
                InvoiceItem.objects.create(
                    invoice=invoice,
                    part=part,
                    name=part.name_ru or part.name,
                    part_number=part.part_number,
                    quantity=actual_qty,
                    unit='шт',
                    price=price,
                    sum=line_sum,
                    price_without_vat=part.price,
                    vat_rate=VAT_RATE,
                )
                total += line_sum

            if total == 0:
                raise ValueError('Ни одной позиции не оказалось в наличии')

            invoice.total_amount = total
            invoice.save(update_fields=['total_amount'])
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    logger.info('Invoice draft created: id=%d dealer=%s total=%s',
                invoice.id, profile.user.username, total)

    return JsonResponse({
        'ok': True,
        'invoice_id': invoice.id,
        'redirect_url': f'/dealer/invoice/{invoice.id}/?from=checkout',
    })


@never_cache
@dealer_required
@require_http_methods(['POST'])
def dealer_invoice_confirm(request, invoice_id):
    """Подтверждение черновика: атомарно списываем склад + присваиваем номер."""
    profile = request.dealer_profile

    try:
        with transaction.atomic():
            # Блокируем черновик
            invoice = (
                Invoice.objects
                .select_for_update()
                .filter(id=invoice_id, dealer=profile, number__isnull=True)
                .first()
            )
            if not invoice:
                return JsonResponse({
                    'ok': False, 'error': 'Черновик не найден или уже подтверждён'
                }, status=404)

            items = list(invoice.items.all())
            if not items:
                return JsonResponse({'ok': False, 'error': 'Черновик пустой'}, status=400)

            # Блокируем все запчасти которые надо списать
            part_ids = [it.part_id for it in items if it.part_id]
            parts_locked = {
                p.id: p
                for p in SparePart.objects.select_for_update().filter(id__in=part_ids)
            }

            # Проверяем остатки на момент подтверждения (мог истощиться)
            for it in items:
                if not it.part_id:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Запчасть «{it.name}» удалена из каталога',
                    }, status=400)
                part = parts_locked.get(it.part_id)
                if not part or not part.is_active:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Запчасть «{it.name}» больше не доступна',
                    }, status=400)
                if part.quantity < it.quantity:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Недостаточно «{it.name}» на складе. Доступно: {part.quantity}, требуется: {it.quantity}',
                    }, status=400)

            # Цена могла поменяться, пока дилер смотрел черновик. Подтверждать
            # по старой цене нельзя — обновляем черновик и просим проверить заново.
            # Return внутри atomic без исключения → обновлённый черновик коммитится.
            changed_names = []
            for it in items:
                part = parts_locked[it.part_id]
                new_price = part.price_with_vat
                if new_price != it.price or part.price != it.price_without_vat:
                    it.price = new_price
                    it.sum = (new_price * it.quantity).quantize(Decimal('0.01'))
                    it.price_without_vat = part.price
                    it.vat_rate = VAT_RATE
                    it.save(update_fields=['price', 'sum', 'price_without_vat', 'vat_rate'])
                    changed_names.append(it.name)
            if changed_names:
                invoice.total_amount = sum((it.sum for it in items), Decimal('0'))
                invoice.save(update_fields=['total_amount'])
                return JsonResponse({
                    'ok': False,
                    'reload': True,
                    'error': 'Изменилась цена: ' + ', '.join(f'«{n}»' for n in changed_names)
                             + '. Счёт пересчитан — проверьте сумму и подтвердите ещё раз.',
                }, status=409)

            # Списываем со склада через F() — атомарно, с записью в журнал склада
            for it in items:
                change_stock(
                    it.part_id, -it.quantity, StockMovement.REASON_ORDER,
                    invoice=invoice, changed_by=profile.user.username,
                )

            # Номер — следующий внутри текущего договора дилера (1, 2, 3…).
            # Блокируем профиль дилера: сериализует параллельные подтверждения
            # и сброс договора сервисом.
            DealerProfile.objects.select_for_update().filter(pk=profile.pk).first()
            contract = current_contract(profile)
            contract.last_number += 1
            contract.save(update_fields=['last_number'])

            # localdate — год по TIME_ZONE (Ташкент): при USE_TZ=True timezone.now()
            # в UTC, и заказ 1 января до 05:00 получил бы год прошлого.
            invoice.year = timezone.localdate().year
            invoice.number = contract.last_number
            invoice.contract = contract
            # Реквизиты договора — на момент подтверждения (договор мог смениться после черновика)
            invoice.buyer_contract_number = contract.number
            invoice.buyer_contract_date = contract.date
            invoice.confirmed_at = timezone.now()
            # Дальше заказ сначала проверяет сервис, бухгалтерия его пока не видит
            invoice.status = Invoice.STATUS_PENDING_APPROVAL
            invoice.save(update_fields=[
                'year', 'number', 'contract', 'buyer_contract_number',
                'buyer_contract_date', 'confirmed_at', 'status',
            ])
    except IntegrityError:
        # Гонка на UniqueConstraint номера — крайне маловероятна,
        # но если случится — клиент перезагрузит и повторит
        return JsonResponse({'ok': False, 'error': 'Попробуйте ещё раз'}, status=409)

    logger.info('Invoice confirmed: №%d/%d dealer=%s',
                invoice.number, invoice.year, profile.user.username)

    return JsonResponse({
        'ok': True,
        'redirect_url': f'/dealer/invoice/{invoice.id}/?from=confirm',
    })


@never_cache
@dealer_required
@require_http_methods(['POST'])
def dealer_invoice_mark_received(request, invoice_id):
    """Дилер подтверждает что груз получил → статус 'Доставлено'.
    Доступно только для своих счетов, только из статуса 'В пути'.
    """
    profile = request.dealer_profile

    with transaction.atomic():
        invoice = (
            Invoice.objects
            .select_for_update()
            .filter(
                id=invoice_id,
                dealer=profile,
                number__isnull=False,
                status=Invoice.STATUS_IN_TRANSIT,
            )
            .first()
        )
        if not invoice:
            return JsonResponse({
                'ok': False,
                'error': 'Заказ не найден, не ваш, или ещё не в пути',
            }, status=404)

        invoice.status = Invoice.STATUS_DELIVERED
        invoice.save(update_fields=['status'])

    logger.info(
        'Invoice received by dealer: №%d/%d username=%s',
        invoice.number, invoice.year, profile.user.username,
    )
    return JsonResponse({
        'ok': True,
        'new_status': Invoice.STATUS_DELIVERED,
        'new_status_label': invoice.get_status_display(),
    })


# Свой заказ дилер может отменить, пока он не оплачен
DEALER_CANCELLABLE_STATUSES = (Invoice.STATUS_PENDING_APPROVAL, Invoice.STATUS_APPROVED)


def _cancel_order(invoice, profile, reason):
    """Отмена подтверждённого заказа с возвратом на склад. Вызывать в atomic под lock'ом."""
    invoice.set_cancelled(changed_by=profile.user.username, reason=reason)
    invoice.save(update_fields=['status', 'cancelled_at', 'cancelled_by', 'cancel_reason'])
    logger.info(
        'Invoice cancelled: №%d/%d by=%s (%s) reason=%s',
        invoice.number, invoice.year, profile.user.username, profile.role, reason,
    )


@never_cache
@dealer_required
@require_http_methods(['POST'])
def dealer_invoice_cancel_order(request, invoice_id):
    """Дилер отменяет СВОЙ подтверждённый заказ — пока он на подтверждении у сервиса
    или уже подтверждён, но ещё не отправлен.
    Остатки возвращаются на склад, номер счёта остаётся (дыр в нумерации нет).
    """
    profile = request.dealer_profile
    reason = (request.POST.get('reason') or '').strip()

    with transaction.atomic():
        invoice = (
            Invoice.objects
            .select_for_update()
            .filter(
                id=invoice_id,
                dealer=profile,
                number__isnull=False,
                status__in=DEALER_CANCELLABLE_STATUSES,
            )
            .first()
        )
        if not invoice:
            return JsonResponse({
                'ok': False,
                'error': 'Заказ не найден или уже отправлен — отменить его может только поставщик',
            }, status=404)
        _cancel_order(invoice, profile, reason)

    return JsonResponse({'ok': True})


@never_cache
@dealer_required
@require_http_methods(['POST'])
def dealer_invoice_cancel(request, invoice_id):
    """Отмена черновика — удаляет его. Подтверждённые счета удалить нельзя."""
    profile = request.dealer_profile
    deleted, _ = Invoice.objects.filter(
        id=invoice_id, dealer=profile, number__isnull=True,
    ).delete()
    if deleted:
        logger.info('Invoice draft cancelled: id=%d dealer=%s',
                    invoice_id, profile.user.username)
    return JsonResponse({'ok': True})


def _invoice_items_and_totals(invoice, include_removed=False):
    """Позиции и итоги счёта для шаблонов (дилерский счёт, карточка заказа, документ).

    price/sum позиций — с НДС. Цена без НДС и сумма НДС есть только у счетов,
    созданных после введения НДС (у старых price_without_vat пустой → has_vat=False).
    Позиции, убранные сервисом (quantity=0), в документы не попадают —
    их видно только в карточке заказа у сервиса (include_removed=True).
    """
    items = [it for it in invoice.items.all() if include_removed or it.quantity > 0]
    has_vat = bool(items) and all(it.price_without_vat is not None for it in items)
    items_ctx = []
    vat_total = Decimal('0')
    for it in items:
        row = {
            'id': it.id,
            'part_id': it.part_id,
            'original_quantity': it.original_quantity,
            'is_changed': it.is_changed_by_supplier,
            'name': it.name,
            'quantity': it.quantity,
            'unit': it.unit,
            'price_formatted': format_uzs(it.price),
            'sum_formatted': format_uzs(it.sum),
            'price_without_vat_formatted': '',
        }
        if has_vat:
            row['price_without_vat_formatted'] = format_uzs(it.price_without_vat)
            vat_total += it.sum - it.price_without_vat * it.quantity
        items_ctx.append(row)

    vat_rates = {it.vat_rate for it in items if it.vat_rate is not None}
    totals = {
        'amount_formatted': format_uzs(invoice.total_amount),
        'currency': 'UZS',
        'amount_in_words': amount_in_words_uzs(invoice.total_amount),
        'has_vat': has_vat,
        'vat_formatted': format_uzs(vat_total) if has_vat else '',
        # '12' вместо '12.00'
        'vat_rate': (f'{vat_rates.pop().normalize():f}' if len(vat_rates) == 1 else '') if has_vat else '',
    }
    return items_ctx, totals


@never_cache
@dealer_required
def dealer_invoices_list(request):
    """История счетов текущего дилера. Только подтверждённые (без черновиков)."""
    profile = request.dealer_profile
    invoices = (
        Invoice.objects
        .filter(dealer=profile, number__isnull=False)   # черновики скрываем
        .order_by('-confirmed_at', '-id')
    )

    # year/number → строка чтоб Django не вставлял пробел-разделитель тысяч (USE_THOUSAND_SEPARATOR=True)
    items_ctx = [
        {
            'id': inv.id,
            'number': str(inv.number),
            'year': str(inv.year),
            'date': format_date_ru(inv.confirmed_at or inv.created_at),
            'total_formatted': format_uzs(inv.total_amount),
            'contract_number': inv.buyer_contract_number,
            'status': inv.status,
            'status_label': inv.get_status_display(),
        }
        for inv in invoices
    ]

    return render(request, 'main/dealer/invoices_list.html', {
        'profile': profile,
        'invoices': items_ctx,
    })


@never_cache
@dealer_required
@require_http_methods(['GET'])
def dealer_invoice(request, invoice_id):
    """Рендер счёта (черновик или подтверждённый) для своего дилера."""
    profile = request.dealer_profile
    invoice = (
        Invoice.objects
        .filter(id=invoice_id, dealer=profile)
        .prefetch_related('items')
        .first()
    )
    if not invoice:
        messages.warning(request, 'Счёт не найден.')
        return redirect('dealer_shop')

    items_ctx, totals = _invoice_items_and_totals(invoice)

    is_draft = invoice.is_draft
    # Для черновика дата = момент создания; для подтверждённого = confirmed_at
    invoice_date = invoice.created_at if is_draft else (invoice.confirmed_at or invoice.created_at)

    # Дилер может подтвердить получение только если счёт «В пути»
    can_mark_received = (not is_draft) and invoice.status == Invoice.STATUS_IN_TRANSIT
    # Отменить сам — только пока не оплачен
    can_cancel_order = (not is_draft) and invoice.status in DEALER_CANCELLABLE_STATUSES

    # Что поменял сервис: было → стало (в т.ч. убранные позиции)
    supplier_changes = [
        {'name': it.name, 'was': it.original_quantity, 'now': it.quantity}
        for it in invoice.items.all() if it.is_changed_by_supplier
    ]

    return render(request, 'main/dealer/invoice.html', {
        'profile': profile,
        'invoice': {
            'id': invoice.id,
            'is_draft': is_draft,
            # str() — против USE_THOUSAND_SEPARATOR=True ('2026' вместо '2 026')
            'number': str(invoice.number) if invoice.number is not None else '',
            'year': str(invoice.year) if invoice.year is not None else '',
            'date': format_date_ru(invoice_date),
            'status': invoice.status,
            'status_label': invoice.get_status_display(),
            'can_mark_received': can_mark_received,
            'can_cancel_order': can_cancel_order,
            'cancel_reason': invoice.cancel_reason,
            'is_awaiting_approval': invoice.is_awaiting_approval,
        },
        'supplier_changes': supplier_changes,
        'buyer': {
            'name': invoice.buyer_company_name,
            'inn': invoice.buyer_inn,
            'contract_number': invoice.buyer_contract_number,
        },
        'items': items_ctx,
        'totals': totals,
    })


# ========== STAFF (СОТРУДНИКИ СЕРВИСА + БУХГАЛТЕР) ==========

# Правила переходов статусов по ролям.
# Сервис подтверждает заказ и двигает его до "в пути", бухгалтер только смотрит,
# финальный шаг "доставлено" подтверждает САМ ДИЛЕР у себя в счёте.
# Отмена (с возвратом на склад) — сервису и дилеру до отгрузки.
# После "в пути" отменить может только админ (в админке).
ALLOWED_STATUS_TRANSITIONS = {
    # Бухгалтер статусы не меняет — только смотрит счёт и спецификацию
    # (а «На подтверждении» вообще не видит).
    DealerProfile.ROLE_ACCOUNTANT: {},
    DealerProfile.ROLE_SERVICE: {
        # подтвердить заказ (→ бухгалтерии) или отменить
        Invoice.STATUS_PENDING_APPROVAL: [Invoice.STATUS_APPROVED, Invoice.STATUS_CANCELLED],
        Invoice.STATUS_APPROVED: [Invoice.STATUS_IN_TRANSIT, Invoice.STATUS_CANCELLED],
    },
    DealerProfile.ROLE_DEALER: {
        Invoice.STATUS_PENDING_APPROVAL: [Invoice.STATUS_CANCELLED],
        Invoice.STATUS_APPROVED: [Invoice.STATUS_CANCELLED],
        Invoice.STATUS_IN_TRANSIT:      [Invoice.STATUS_DELIVERED],
    },
}


def _allowed_next_statuses(profile, current_status):
    """Доступные статусы для смены, исходя из роли и текущего."""
    return ALLOWED_STATUS_TRANSITIONS.get(profile.role, {}).get(current_status, [])


def _staff_invoices(profile):
    """Подтверждённые дилерами заказы, которые видит сотрудник.
    Бухгалтер не видит заказы, которые ещё не подтвердил сервис."""
    qs = Invoice.objects.filter(number__isnull=False)
    if not profile.is_service:
        qs = qs.exclude(status=Invoice.STATUS_PENDING_APPROVAL)
    return qs


@never_cache
@staff_required
def staff_orders_list(request):
    """Список ВСЕХ подтверждённых заказов — общий для сервиса и бухгалтера.
    Фильтры: ?status=, ?q= (по номеру / имени дилера / ИНН)
    """
    profile = request.dealer_profile
    qs = (
        _staff_invoices(profile)
        .select_related('dealer')
        .order_by('-confirmed_at', '-id')
    )

    status_filter = (request.GET.get('status') or '').strip()
    q = (request.GET.get('q') or '').strip()

    status_choices = [
        (value, label) for value, label in Invoice.STATUS_CHOICES
        if profile.is_service or value != Invoice.STATUS_PENDING_APPROVAL
    ]
    awaiting_count = (
        qs.filter(status=Invoice.STATUS_PENDING_APPROVAL).count() if profile.is_service else 0
    )

    if status_filter and status_filter in dict(status_choices):
        qs = qs.filter(status=status_filter)

    if q:
        # Если строка — число → ищем по номеру; иначе — по имени/ИНН
        if q.isdigit():
            qs = qs.filter(number=int(q))
        else:
            qs = qs.filter(
                Q(buyer_company_name__icontains=q)
                | Q(buyer_inn__icontains=q)
                | Q(dealer__name__icontains=q)
            )

    items_ctx = [
        {
            'id': inv.id,
            'number': str(inv.number),
            'year': str(inv.year),
            'date': format_date_ru(inv.confirmed_at or inv.created_at),
            'dealer_name': inv.dealer.name,
            'buyer_company_name': inv.buyer_company_name,
            'total_formatted': format_uzs(inv.total_amount),
            'status': inv.status,
            'status_label': inv.get_status_display(),
        }
        for inv in qs[:200]   # ограничиваем — пагинация будет позже
    ]

    return render(request, 'main/dealer/staff_orders.html', {
        'profile': profile,
        'invoices': items_ctx,
        'status_filter': status_filter,
        'search_query': q,
        'status_choices': status_choices,
        'awaiting_count': awaiting_count,
        'awaiting_status': Invoice.STATUS_PENDING_APPROVAL,
    })


@never_cache
@staff_required
def staff_order_detail(request, invoice_id):
    """Просмотр конкретного заказа сотрудником + доступные действия по статусу."""
    profile = request.dealer_profile
    invoice = (
        _staff_invoices(profile)
        .filter(id=invoice_id)
        .select_related('dealer')
        .prefetch_related('items')
        .first()
    )
    if not invoice:
        messages.warning(request, 'Заказ не найден.')
        return redirect('staff_orders_list')

    # Количество правит только сервис и только до своего подтверждения
    can_edit_items = profile.is_service and invoice.is_awaiting_approval
    items_ctx, totals = _invoice_items_and_totals(invoice, include_removed=can_edit_items)
    if can_edit_items:
        # Максимум = уже заказано (списано) + свободный остаток на складе
        stock = dict(
            SparePart.objects.filter(id__in=[r['part_id'] for r in items_ctx if r['part_id']])
            .values_list('id', 'quantity')
        )
        for row in items_ctx:
            row['stock'] = stock.get(row['part_id'])
            row['max_quantity'] = row['quantity'] + (row['stock'] or 0)

    # Какие переходы доступны этой роли с текущего статуса
    next_options = [
        {'value': s, 'label': dict(Invoice.STATUS_CHOICES)[s]}
        for s in _allowed_next_statuses(profile, invoice.status)
    ]

    return render(request, 'main/dealer/staff_order_detail.html', {
        'profile': profile,
        'invoice': {
            'id': invoice.id,
            'number': str(invoice.number),
            'year': str(invoice.year),
            'date': format_date_ru(invoice.confirmed_at or invoice.created_at),
            'dealer_name': invoice.dealer.name,
            'status': invoice.status,
            'status_label': invoice.get_status_display(),
            'cancelled_by': invoice.cancelled_by,
            'cancelled_at': format_date_ru(invoice.cancelled_at) if invoice.cancelled_at else '',
            'cancel_reason': invoice.cancel_reason,
            'approved_by': invoice.approved_by,
            'approved_at': format_date_ru(invoice.approved_at) if invoice.approved_at else '',
        },
        'buyer': {
            'name': invoice.buyer_company_name,
            'inn': invoice.buyer_inn,
            'contract_number': invoice.buyer_contract_number,
        },
        'items': items_ctx,
        'totals': totals,
        'next_options': next_options,
        'can_edit_items': can_edit_items,
        'has_supplier_changes': any(r['is_changed'] for r in items_ctx),
    })


@never_cache
@service_required
@require_http_methods(['POST'])
def staff_order_update_items(request, invoice_id):
    """Сервис меняет количество позиций заказа, пока не подтвердил его.

    JSON {"items": [{"id": <InvoiceItem.id>, "quantity": N}, ...]}.
    Разница сразу двигает склад (журнал: «Правка заказа сервисом»): уменьшили — вернули
    на склад, увеличили — списали (не больше свободного остатка). 0 — позиция убрана.
    Цена остаётся та, по которой заказывал дилер.
    """
    profile = request.dealer_profile
    try:
        payload = json.loads(request.body or b'{}')
        requested = {}
        for row in payload.get('items', [])[:200]:
            qty = int(row['quantity'])
            if qty < 0 or qty > 100000:
                raise ValueError
            requested[int(row['id'])] = qty
    except (ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'error': 'Неверные данные'}, status=400)

    username = profile.user.username
    changed = []
    with transaction.atomic():
        invoice = (
            Invoice.objects.select_for_update()
            .filter(id=invoice_id, number__isnull=False, status=Invoice.STATUS_PENDING_APPROVAL)
            .first()
        )
        if not invoice:
            return JsonResponse({
                'ok': False, 'error': 'Заказ не найден или уже подтверждён — количество менять нельзя',
            }, status=404)

        items = {it.id: it for it in invoice.items.all()}
        if set(requested) - set(items):
            return JsonResponse({'ok': False, 'error': 'Позиция не из этого заказа'}, status=400)

        to_change = {iid: q for iid, q in requested.items() if items[iid].quantity != q}
        if to_change and all(to_change.get(iid, it.quantity) == 0 for iid, it in items.items()):
            return JsonResponse({
                'ok': False,
                'error': 'Нельзя убрать все позиции. Если заказ не нужен — отмените его.',
            }, status=400)

        parts = {
            p.id: p for p in SparePart.objects.select_for_update()
            .filter(id__in=[items[i].part_id for i in to_change if items[i].part_id])
        }
        # Сначала проверяем всё, потом двигаем склад
        for iid, new_qty in to_change.items():
            it = items[iid]
            delta = new_qty - it.quantity
            if delta > 0:
                part = parts.get(it.part_id)
                if not part:
                    return JsonResponse({
                        'ok': False, 'error': f'«{it.name}» удалена из каталога — увеличить нельзя',
                    }, status=400)
                if part.quantity < delta:
                    return JsonResponse({
                        'ok': False,
                        'error': f'«{it.name}»: на складе свободно {part.quantity}, '
                                 f'можно максимум {it.quantity + part.quantity}',
                    }, status=400)

        for iid, new_qty in to_change.items():
            it = items[iid]
            old_qty = it.quantity
            if it.part_id in parts:
                # уменьшили → вернули на склад (+), увеличили → списали (−)
                change_stock(
                    it.part_id, old_qty - new_qty, StockMovement.REASON_ORDER_EDIT,
                    invoice=invoice, changed_by=username,
                    comment=f'Заказ №{invoice.number}/{invoice.year}: {old_qty} → {new_qty}',
                )
            if it.original_quantity is None:
                it.original_quantity = old_qty
            it.quantity = new_qty
            it.sum = (it.price * new_qty).quantize(Decimal('0.01'))
            it.save(update_fields=['quantity', 'original_quantity', 'sum'])
            changed.append(f'{it.part_number or it.name}: {old_qty}→{new_qty}')

        if changed:
            invoice.total_amount = sum((it.sum for it in items.values()), Decimal('0'))
            invoice.save(update_fields=['total_amount'])

    if changed:
        logger.info('Order items edited: invoice=№%d/%d by=%s %s',
                    invoice.number, invoice.year, username, ', '.join(changed))
    return JsonResponse({'ok': True, 'changed': len(changed)})


@never_cache
@staff_required
@require_http_methods(['POST'])
def staff_change_status(request, invoice_id):
    """Смена статуса заказа.
    Сервис: на подтверждении → подтверждён → в пути (delivered ставит дилер).
    Бухгалтер статусы не меняет.
    Отмена — по матрице ALLOWED_STATUS_TRANSITIONS, с возвратом остатков на склад.
    Любой другой переход — 403.
    """
    profile = request.dealer_profile
    new_status = (request.POST.get('status') or '').strip()
    reason = (request.POST.get('reason') or '').strip()

    if new_status not in dict(Invoice.STATUS_CHOICES):
        return JsonResponse({'ok': False, 'error': 'Неизвестный статус'}, status=400)

    with transaction.atomic():
        invoice = (
            _staff_invoices(profile)
            .select_for_update()
            .filter(id=invoice_id)
            .first()
        )
        if not invoice:
            return JsonResponse({'ok': False, 'error': 'Заказ не найден'}, status=404)

        allowed = _allowed_next_statuses(profile, invoice.status)
        if new_status not in allowed:
            return JsonResponse({
                'ok': False,
                'error': 'У вашей роли нет права на этот переход',
            }, status=403)

        if new_status == Invoice.STATUS_CANCELLED:
            _cancel_order(invoice, profile, reason)
            return JsonResponse({
                'ok': True,
                'new_status': new_status,
                'new_status_label': invoice.get_status_display(),
            })

        update_fields = ['status']
        if invoice.status == Invoice.STATUS_PENDING_APPROVAL:
            # Сервис подтверждает заказ → его видит бухгалтерия, дилеру выдаётся счёт
            if not invoice.items.filter(quantity__gt=0).exists():
                return JsonResponse({
                    'ok': False, 'error': 'В заказе не осталось позиций — отмените его',
                }, status=400)
            invoice.approved_at = timezone.now()
            invoice.approved_by = profile.user.username
            update_fields += ['approved_at', 'approved_by']
        invoice.status = new_status
        invoice.save(update_fields=update_fields)

    logger.info(
        'Status changed: invoice=№%d/%d by=%s (%s) → %s',
        invoice.number, invoice.year, profile.user.username, profile.role, new_status,
    )
    return JsonResponse({
        'ok': True,
        'new_status': new_status,
        'new_status_label': invoice.get_status_display(),
    })


@never_cache
@staff_required
def staff_invoice_view(request, invoice_id):
    """Рендер ПОЛНОГО документа счёта для сотрудника (тот же шаблон что у дилера).
    Никаких действий: ни «Получил», ни смены статуса — только просмотр и печать.
    """
    profile = request.dealer_profile
    invoice = (
        _staff_invoices(profile)
        .filter(id=invoice_id)
        .prefetch_related('items')
        .first()
    )
    if not invoice:
        messages.warning(request, 'Счёт не найден.')
        return redirect('staff_orders_list')

    items_ctx, totals = _invoice_items_and_totals(invoice)
    invoice_date = invoice.confirmed_at or invoice.created_at

    return render(request, 'main/dealer/invoice.html', {
        'profile': profile,
        'invoice': {
            'id': invoice.id,
            'is_draft': False,
            'number': str(invoice.number),
            'year': str(invoice.year),
            'date': format_date_ru(invoice_date),
            'status': invoice.status,
            'status_label': invoice.get_status_display(),
            'can_mark_received': False,         # сотрудник не дилер
            'cancel_reason': invoice.cancel_reason,
            'back_url': reverse('staff_order_detail', args=[invoice.id]),
            'back_label': '← К управлению заказом',
        },
        'buyer': {
            'name': invoice.buyer_company_name,
            'inn': invoice.buyer_inn,
            'contract_number': invoice.buyer_contract_number,
        },
        'items': items_ctx,
        'totals': totals,
    })


def _spec_amount(amount):
    """Сумма для спецификации: '370 720' (без копеек, если их нет), иначе '246 400,50'."""
    if amount is None:
        return '—'
    s = format_uzs(amount)
    return s[:-3] if s.endswith(',00') else s


@never_cache
@staff_required
def staff_specification_view(request, invoice_id):
    """Спецификация к договору по заказу — для печати (A4). Только просмотр.

    Номер спецификации = номер счёта, дата = дата подтверждения заказа.
    Цена без НДС берётся из снапшота позиции; у заказов до введения НДС её нет → «—».
    """
    invoice = (
        _staff_invoices(request.dealer_profile)
        .filter(id=invoice_id)
        .prefetch_related('items__part')
        .first()
    )
    if not invoice:
        messages.warning(request, 'Заказ не найден.')
        return redirect('staff_orders_list')

    items = [it for it in invoice.items.all() if it.quantity > 0]   # убранные сервисом не печатаем
    items_ctx = [
        {
            'name': it.name,
            # У позиций до появления снапшота кода — берём из самой запчасти, если она жива
            'part_number': it.part_number or (it.part.part_number if it.part else ''),
            'quantity': it.quantity,
            'price_without_vat': _spec_amount(it.price_without_vat),
            'price': _spec_amount(it.price),
            'sum': _spec_amount(it.sum),
        }
        for it in items
    ]

    spec_date = timezone.localtime(invoice.confirmed_at or invoice.created_at)
    contract_date = invoice.buyer_contract_date
    return render(request, 'main/dealer/specification.html', {
        'spec': {
            'number': str(invoice.number),
            'day': f'{spec_date.day:02d}',
            'month': MONTHS_RU_GENITIVE[spec_date.month - 1].capitalize(),
            'year': str(spec_date.year),
            'contract_number': invoice.buyer_contract_number,
            'contract_date': contract_date.strftime('%d.%m.%Y') if contract_date else '',
            'buyer_name': invoice.buyer_company_name,
            'status': invoice.status,
            'status_label': invoice.get_status_display(),
            'back_url': reverse('staff_order_detail', args=[invoice.id]),
        },
        'items': items_ctx,
        'total_quantity': str(sum(it.quantity for it in items)),
        'total_amount': _spec_amount(invoice.total_amount),
    })


@never_cache
@service_required
def staff_contracts(request):
    """Договоры дилеров — только сервис. Здесь заводится новый договор:
    номер + дата → нумерация счетов и спецификаций дилера начинается с №1.
    """
    profile = request.dealer_profile
    q = (request.GET.get('q') or '').strip()

    dealers = DealerProfile.objects.filter(role=DealerProfile.ROLE_DEALER).order_by('name')
    if q:
        dealers = dealers.filter(
            Q(name__icontains=q) | Q(company_name__icontains=q)
            | Q(inn__icontains=q) | Q(contract_number__icontains=q)
        )
    dealers = list(dealers[:300])

    latest = {}
    for c in DealerContract.objects.filter(dealer__in=dealers).order_by('dealer_id', '-created_at', '-id'):
        latest.setdefault(c.dealer_id, c)

    rows = []
    for d in dealers:
        c = latest.get(d.id)
        rows.append({
            'id': d.id,
            'name': d.name,
            'company_name': d.company_name,
            'inn': d.inn,
            'is_active': d.is_active,
            'contract_number': c.number if c else d.contract_number,
            'contract_date': format_date_ru(c.date if c else d.contract_date),
            'last_number': str(c.last_number) if c else '0',
            'started_at': format_date_ru(c.created_at) if c and c.created_by != 'auto' else '',
            'started_by': c.created_by if c and c.created_by != 'auto' else '',
        })

    return render(request, 'main/dealer/staff_contracts.html', {
        'profile': profile,
        'rows': rows,
        'q': q,
        'done_id': request.GET.get('done', ''),
    })


@never_cache
@service_required
@require_http_methods(['POST'])
def staff_contract_new(request, dealer_id):
    """Новый договор дилера: номер + дата, нумерация счетов/спецификаций — с №1."""
    profile = request.dealer_profile
    number = (request.POST.get('contract_number') or '').strip()[:100]
    raw_date = (request.POST.get('contract_date') or '').strip()

    try:
        contract_date = datetime.strptime(raw_date, '%Y-%m-%d').date() if raw_date else None
    except ValueError:
        contract_date = None
    if not number or not contract_date:
        messages.error(request, 'Укажите номер и дату договора.')
        return redirect('staff_contracts')

    with transaction.atomic():
        dealer = (
            DealerProfile.objects.select_for_update()
            .filter(pk=dealer_id, role=DealerProfile.ROLE_DEALER)
            .first()
        )
        if not dealer:
            messages.error(request, 'Дилер не найден.')
            return redirect('staff_contracts')
        DealerContract.objects.create(
            dealer=dealer, number=number, date=contract_date,
            created_by=profile.user.username,
        )
        dealer.contract_number = number
        dealer.contract_date = contract_date
        dealer.save(update_fields=['contract_number', 'contract_date', 'updated_at'])

    logger.info('New dealer contract: dealer=%s number=%s date=%s by=%s',
                dealer.user.username, number, contract_date, profile.user.username)
    return redirect(f"{reverse('staff_contracts')}?done={dealer.id}")


@never_cache
@service_required
def staff_parts_list(request):
    """Список всех запчастей — только для сервиса. Можно править остаток."""
    profile = request.dealer_profile
    q = (request.GET.get('q') or '').strip()

    parts = SparePart.objects.select_related('type').prefetch_related('parent_models').order_by('part_number')
    if q:
        parts = parts.filter(
            Q(part_number__icontains=q)
            | Q(name__icontains=q)
            | Q(name_ru__icontains=q)
        )

    items_ctx = [
        {
            'id': p.id,
            'part_number': p.part_number,
            'name': p.name_ru or p.name,
            'type': (p.type.name_ru or p.type.name) if p.type_id else '—',
            'parent_models': ', '.join(pm.name for pm in p.parent_models.all()) or '—',
            'quantity': p.quantity,
            'price_formatted': format_uzs(p.price_with_vat),
            'price_without_vat_formatted': format_uzs(p.price),
            'is_active': p.is_active,
        }
        for p in parts[:500]
    ]

    return render(request, 'main/dealer/staff_parts.html', {
        'profile': profile,
        'parts': items_ctx,
        'search_query': q,
    })


@never_cache
@service_required
@require_http_methods(['POST'])
def staff_part_update_quantity(request, part_id):
    """POST. Установить новое значение количества запчасти (или прирастить).

    Тело: {"quantity": <int>} — устанавливает новое значение.
            ИЛИ {"delta": <int>} — прирост (можно и отрицательный).
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Некорректный JSON'}, status=400)

    new_quantity = payload.get('quantity', None)
    delta = payload.get('delta', None)

    with transaction.atomic():
        part = SparePart.objects.select_for_update().filter(id=part_id).first()
        if not part:
            return JsonResponse({'ok': False, 'error': 'Запчасть не найдена'}, status=404)
        old_quantity = part.quantity

        if new_quantity is not None:
            try:
                new_quantity = int(new_quantity)
                if new_quantity < 0:
                    raise ValueError
            except (TypeError, ValueError):
                return JsonResponse({'ok': False, 'error': 'quantity должен быть ≥ 0'}, status=400)
            part.quantity = new_quantity
        elif delta is not None:
            try:
                delta = int(delta)
            except (TypeError, ValueError):
                return JsonResponse({'ok': False, 'error': 'delta должен быть числом'}, status=400)
            new_val = part.quantity + delta
            if new_val < 0:
                return JsonResponse({
                    'ok': False,
                    'error': f'Нельзя уйти в минус (текущий остаток: {part.quantity})',
                }, status=400)
            part.quantity = new_val
        else:
            return JsonResponse({'ok': False, 'error': 'Нужен quantity или delta'}, status=400)

        part.save(update_fields=['quantity'])
        record_stock_change(
            part.id, part.quantity - old_quantity, part.quantity,
            StockMovement.REASON_STAFF, changed_by=request.dealer_profile.user.username,
        )

    logger.info('Stock updated: part=%s qty=%d by=%s',
                part.part_number, part.quantity, request.dealer_profile.user.username)
    return JsonResponse({'ok': True, 'quantity': part.quantity})


def product_detail(request, product_id):
    return render(request, 'main/product_detail.html', {'product_id': product_id})


def privacy_policy_mobile(request):
    """Политика конфиденциальности мобильного приложения VUM ERP.
    Standalone-страница с переключателем языков RU/UZ/EN (внутри шаблона)."""
    return render(request, 'main/mobile/privacy-policy-mobile.html')


def become_a_dealer(request):
    try:
        page_data = BecomeADealerPage.get_instance()
        
        context = {
            'page_data': page_data,
            'requirements': page_data.requirements.all().order_by('order')
        }
        return render(request, 'main/become_a_dealer.html', context)
    
    except Exception as e:
        logger.error(f"Ошибка на странице 'Стать дилером': {str(e)}", exc_info=True)
        return render(request, 'main/become_a_dealer.html', {'page_data': None})


def lizing(request):
    return render(request, 'main/lizing.html')


def news(request):
    """Страница со всеми новостями"""
    try:
        news_list = News.objects.filter(
            is_active=True
        ).select_related('author').order_by('-order', '-created_at')
        
        return render(request, 'main/news.html', {'news_list': news_list})
    
    except Exception as e:
        logger.error(f"Ошибка на странице новостей: {str(e)}", exc_info=True)
        return render(request, 'main/news.html', {'news_list': []})


def dealers(request):
    return render(request, 'main/dealers.html')


def jobs(request):
    """Страница с вакансиями"""
    try:
        from .serializers import VacancySerializer
        
        vacancies = Vacancy.objects.filter(is_active=True).order_by('order', '-created_at')
        
        serializer = VacancySerializer(vacancies, many=True, context={'request': request})
        vacancies_data = serializer.data
        
        return render(request, 'main/jobs.html', {
            'vacancies': vacancies,
            'vacancies_data': vacancies_data
        })
    
    except Exception as e:
        logger.error(f"Ошибка на странице вакансий: {str(e)}", exc_info=True)
        return render(request, 'main/jobs.html', {'vacancies': [], 'vacancies_data': []})


def news_detail(request, slug):
    """Детальная страница новости"""
    try:
        news = get_object_or_404(
            News.objects.prefetch_related('blocks'), 
            slug=slug, 
            is_active=True
        )
        
        language = getattr(request, 'LANGUAGE_CODE', 'uz')
        breadcrumbs = {
            'uz': {
                'home': 'Bosh sahifa',
                'news': 'VUM yangiliklar',
                'current': news.title_uz if hasattr(news, 'title_uz') else news.title
            },
            'ru': {
                'home': 'Главная',
                'news': 'Новости VUM',
                'current': news.title_ru if hasattr(news, 'title_ru') else news.title
            },
            'en': {
                'home': 'Home',
                'news': 'VUM News',
                'current': news.title_en if hasattr(news, 'title_en') else news.title
            }
        }
        
        return render(request, 'main/news_detail.html', {
            'news': news,
            'blocks': news.blocks.all(),
            'breadcrumbs': breadcrumbs.get(language, breadcrumbs['uz'])
        })
    
    except Exception as e:
        logger.error(f"Ошибка на странице новости {slug}: {str(e)}", exc_info=True)
        return redirect('news')


# === API ViewSets ===

class NewsViewSet(viewsets.ModelViewSet):
    """API endpoint для CRUD операций с новостями"""
    serializer_class = NewsSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return News.objects.select_related('author').prefetch_related('blocks').order_by('-created_at')


class ContactFormViewSet(viewsets.ModelViewSet):
    """API для контактных форм FAW.UZ"""
    queryset = ContactForm.objects.all().order_by('-created_at')
    serializer_class = ContactFormSerializer
    
    # ✅ ИСПРАВЛЕНО: Разные права для разных методов
    def get_permissions(self):
        if self.action in ['create']:
            # POST требует CSRF в headers
            return [AllowAny()]
        else:
            # GET/PUT/DELETE только для админов
            return [IsAdminUser()]
    
    def get_queryset(self):
        """Оптимизация: загружаем с select_related"""
        return ContactForm.objects.all().order_by('-created_at')
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'region', 'amocrm_status'] 
    search_fields = ['name', 'phone']
    ordering_fields = ['created_at', 'priority']
    
    
    def create(self, request, *args, **kwargs):
        try:
            # ============ ПРОВЕРКА reCAPTCHA ============
            recaptcha_token = request.data.get('recaptcha_token')
            
            if settings.RECAPTCHA_ENABLED:
                client_ip = get_client_ip(request)
                recaptcha_result = verify_recaptcha(
                    token=recaptcha_token,
                    action='contact_form',
                    remote_ip=client_ip
                )
                
                if not recaptcha_result['success']:
                    score = recaptcha_result.get('score', 'N/A')
                    error_msg = recaptcha_result['error']
                    logger.critical(
                        f"🚫 reCAPTCHA FAILED: score={score}, threshold=0.1, error={error_msg}, action={recaptcha_result.get('action')}"
                    )
                    return Response({
                        'success': False,
                        'message': f'Verification failed: {error_msg}',
                        'errors': {'recaptcha': error_msg}
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                logger.info(f"✅ reCAPTCHA passed: score={recaptcha_result['score']}")
            
            # ============ ВАЛИДАЦИЯ ФОРМЫ ============
            serializer = self.get_serializer(data=request.data)
            
            if not serializer.is_valid():
                logger.warning(f"Validation errors in ContactForm: {serializer.errors}")
                return Response({
                    'success': False,
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ============ СОХРАНЕНИЕ ============
            contact_form = serializer.save()
            logger.info(f"✅ ContactForm created: #{contact_form.id}")
            
            # ============ ОТПРАВКА В amoCRM ============
            try:
                from main.services.amocrm.lead_sender import LeadSender
                LeadSender.send_lead(contact_form)
                contact_form.refresh_from_db()
                logger.info(f"✅ Lead sent to amoCRM: #{contact_form.id}")
            except Exception as amocrm_error:
                logger.error(
                    f"Ошибка amoCRM для лида #{contact_form.id}: {str(amocrm_error)}", 
                    exc_info=True
                )
            
            # ============ ОТПРАВКА В TELEGRAM ============
            try:
                from main.services.telegram import TelegramNotificationSender
                TelegramNotificationSender.send_lead_notification(contact_form)
                logger.info(f"✅ Telegram notification sent: #{contact_form.id}")
            except Exception as telegram_error:
                logger.error(
                    f"Ошибка Telegram для лида #{contact_form.id}: {str(telegram_error)}", 
                    exc_info=True
                )
            
            return Response({
                'success': True,
                'message': 'Xabar yuborildi!'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка создания формы: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class JobApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint для приема заявок на вакансии"""
    serializer_class = JobApplicationSerializer
    
    def get_queryset(self):
        """✅ Оптимизация: загружаем вакансию сразу"""
        return JobApplication.objects.select_related('vacancy').order_by('-created_at')
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        else:
            return [IsAdminUser()]
    
    def create(self, request, *args, **kwargs):
        try:
            # ============ ПРОВЕРКА reCAPTCHA ============
            recaptcha_token = request.data.get('recaptcha_token')
            
            if settings.RECAPTCHA_ENABLED:
                client_ip = get_client_ip(request)
                recaptcha_result = verify_recaptcha(
                    token=recaptcha_token,
                    action='job_application',
                    remote_ip=client_ip
                )
                
                if not recaptcha_result['success']:
                    score = recaptcha_result.get('score', 'N/A')
                    logger.warning(
                        f"🚫 reCAPTCHA failed for job application: score={score}, error={recaptcha_result['error']}"
                    )
                    return Response({
                        'success': False,
                        'message': 'Подозрительная активность. Попробуйте позже.',
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # ============ ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ ============
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                'success': True,
                'message': 'Rezyume muvaffaqiyatli yuborildi! Tez orada siz bilan bog\'lanamiz.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Ошибка создания заявки на вакансию: {str(e)}", exc_info=True)
            return Response({
                'success': False, 
                'message': 'Xatolik yuz berdi'
            }, status=500)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """API для продуктов FAW"""
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        try:
            queryset = Product.objects.filter(is_active=True).prefetch_related(
                'card_specs__icon',   
                'parameters',          
                'features__icon',     
                'gallery'             
            ).order_by('order', 'title')
            
            category = self.request.query_params.get('category', None)
            if category:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(category=category) | Q(categories__icontains=category)
                )
            
            return queryset
        except Exception as e:
            logger.error(f"Ошибка получения продуктов: {str(e)}", exc_info=True)
            return Product.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductCardSerializer

def products(request):
    """Страница со списком продуктов по категориям"""
    try:
        category = request.GET.get('category', 'tiger_vh')
        
        CATEGORY_DATA = {
            'samosval': {
                'title': 'Samosvallar',
                'title_ru': 'Самосвалы',
                'title_en': 'Dump Trucks',
                'slogan': 'Kuchli va ishonchli yuk tashish uchun mo\'ljallangan samosval avtomashinalar',
                'slogan_ru': 'Самосвальные грузовики для мощных и надежных перевозок',
                'slogan_en': 'Dump trucks for powerful and reliable transportation',
                'hero_image': 'images/slider-foto_img/1.png',
                'breadcrumb': 'Samosvallar'
            },
            'shassi': {
                'title': 'Shassilar',
                'title_ru': 'Шасси',
                'title_en': 'Chassis',
                'slogan': 'Turli maxsus qurilmalar o\'rnatish uchun mustahkam va ishonchli shassi',
                'slogan_ru': 'Прочное и надежное шасси для установки различного специального оборудования',
                'slogan_en': 'Strong and reliable chassis for mounting various special equipment',
                'hero_image': 'images/slider-foto_img/2.png',
                'breadcrumb': 'Shassilar'
            },
            'furgon': {
                'title': 'Avtofurgonlar',
                'title_ru': 'Фургоны',
                'title_en': 'Vans',
                'slogan': 'Xavfsiz va qulay yuk tashish uchun yopiq kuzovli avtomobillar',
                'slogan_ru': 'Закрытые фургоны для безопасной и удобной перевозки грузов',
                'slogan_en': 'Enclosed vans for safe and convenient cargo transportation',
                'hero_image': 'images/slider-foto_img/4.png',
                'breadcrumb': 'Avtofurgonlar'
            },
            'maxsus': {
                'title': 'Maxsus texnika',
                'title_ru': 'Спецтехника',
                'title_en': 'Special Equipment',
                'slogan': 'Maxsus vazifalarni bajarish uchun mo\'ljallangan keng turdagi texnika',
                'slogan_ru': 'Широкий ассортимент техники для выполнения специальных задач',
                'slogan_en': 'Wide range of equipment for special tasks',
                'hero_image': 'images/slider-foto_img/5.png',
                'breadcrumb': 'Maxsus texnika'
            },
            'tiger_v': {
                'title': 'FAW Tiger V',
                'title_ru': 'FAW Tiger V',
                'title_en': 'FAW Tiger V',
                'slogan': 'Zamonaviy texnologiyalar bilan jihozlangan Tiger V modeli',
                'slogan_ru': 'Модель Tiger V с современными технологиями',
                'slogan_en': 'Tiger V model with modern technologies',
                'hero_image': 'images/slider-foto_img/5.png',
                'breadcrumb': 'FAW Tiger V'
            },
            'tiger_vr': {
                'title': 'FAW Tiger VR',
                'title_ru': 'FAW Tiger VR',
                'title_en': 'FAW Tiger VR',
                'slogan': 'Yuqori sifatli Tiger VR modeli',
                'slogan_ru': 'Высококачественная модель Tiger VR',
                'slogan_en': 'High-quality Tiger VR model',
                'hero_image': 'images/slider-foto_img/5.png',
                'breadcrumb': 'FAW Tiger VR'
            },
            'tiger_vh': {
                'title': 'FAW Tiger VH',
                'title_ru': 'FAW Tiger VH',
                'title_en': 'FAW Tiger VH',
                'slogan': 'Ikki yoqilg\'ida harakatlanuvchi texnika',
                'slogan_ru': 'Техника, работающая на двух видах топлива',
                'slogan_en': 'Equipment operating on two types of fuel',
                'hero_image': 'images/vh_models.png',
                'breadcrumb': 'FAW Tiger VH'
            },
        }
        
        category_info = CATEGORY_DATA.get(category, CATEGORY_DATA['tiger_vh'])

        # Вычисляем диапазон цен для текущей категории
        from django.db.models import Min, Max
        price_range = Product.objects.filter(
            category=category,
            is_active=True,
            price__isnull=False
        ).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )

        return render(request, 'main/products.html', {
            'category': category,
            'category_info': category_info,
            'price_range': price_range
        })
    except Exception as e:
        logger.error(f"Ошибка на странице продуктов: {str(e)}", exc_info=True)
        return render(request, 'main/products.html', {
            'category': 'tiger_vh', 
            'category_info': {}
        })


class DealerViewSet(viewsets.ReadOnlyModelViewSet):
    """API для дилеров FAW"""
    serializer_class = DealerSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['city', 'services__slug']
    search_fields = ['name', 'city', 'address']
    
    def get_queryset(self):
        return Dealer.objects.filter(is_active=True).prefetch_related('services').order_by('order', 'city')


class DealerServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DealerService.objects.filter(is_active=True).order_by('order')
    serializer_class = DealerServiceSerializer
    permission_classes = [AllowAny]


class BecomeADealerPageViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    def list(self, request):
        try:
            page = BecomeADealerPage.get_instance()
            serializer = BecomeADealerPageSerializer(page)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Ошибка получения страницы дилерства: {str(e)}", exc_info=True)
            return Response({'error': 'Internal error'}, status=500)


class BecomeADealerApplicationViewSet(viewsets.ModelViewSet):
    queryset = BecomeADealerApplication.objects.all().order_by('-created_at')
    serializer_class = BecomeADealerApplicationSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def create(self, request, *args, **kwargs):
        try:
            # ============ ПРОВЕРКА reCAPTCHA ============
            recaptcha_token = request.data.get('recaptcha_token')
            
            if settings.RECAPTCHA_ENABLED:
                client_ip = get_client_ip(request)
                recaptcha_result = verify_recaptcha(
                    token=recaptcha_token,
                    action='become_dealer',
                    remote_ip=client_ip
                )
                
                if not recaptcha_result['success']:
                    score = recaptcha_result.get('score', 'N/A')
                    logger.warning(
                        f"🚫 reCAPTCHA failed for dealer application: score={score}, error={recaptcha_result['error']}"
                    )
                    return Response({
                        'success': False,
                        'message': 'Подозрительная активность. Попробуйте позже.',
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # ============ ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ ============
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                'success': True,
                'message': "Arizangiz qabul qilindi! Tez orada siz bilan bog'lanamiz."
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Ошибка создания заявки на дилерство: {str(e)}", exc_info=True)
            return Response({
                'success': False, 
                'message': 'Xatolik yuz berdi'
            }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def log_js_error(request):
    """Логирование JS ошибок с фронтенда"""
    try:
        error_data = request.data
        
        message = error_data.get('message', 'Unknown error')
        source = error_data.get('source', 'Unknown source')
        lineno = error_data.get('lineno', 0)
        url = error_data.get('url', 'Unknown URL')
        
        logger.error(
            f"JavaScript Error: {message} | "
            f"Source: {source}:{lineno} | "
            f"Page: {url}",
            extra={'js_error': error_data}
        )
        
        return Response({'status': 'logged'})
    
    except Exception as e:
        logger.error(f"Ошибка логирования JS ошибки: {str(e)}", exc_info=True)
        return Response({'status': 'error'}, status=500)

# ========== DASHBOARD ==========


@staff_member_required
def dashboard_view(request):
    """Главная страница Dashboard с аналитикой"""
    
    # Проверка прав доступа
    if not request.user.is_superuser:
        if not request.user.groups.filter(name__in=['Главные админы', 'Лид-менеджеры']).exists():
            return HttpResponseForbidden('У вас нет доступа к этой странице')
    
    # Получаем параметры фильтров
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    region = request.GET.get('region', '')
    product = request.GET.get('product', '')
    source = request.GET.get('source', '')
    
    # Если дат нет — ставим последние 7 дней
    if not date_from or not date_to:
        tz = timezone.get_current_timezone()
        end_date = timezone.now().astimezone(tz)
        start_date = end_date - timedelta(days=7)
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
    
    # Формируем контекст
    from main.models import REGION_CHOICES
    
    # Получаем список уникальных моделей
    products = ContactForm.objects.exclude(
        Q(product__isnull=True) | Q(product='')
    ).values_list('product', flat=True).distinct().order_by('product')
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'region': region,
        'product': product,
        'source': source,
        'regions': REGION_CHOICES,
        'products': list(products),
    }
    
    return render(request, 'main/dashboard/dashboard.html', context)


@staff_member_required
def dashboard_api_data(request):
    """API endpoint для получения данных dashboard через AJAX"""
    from django.http import JsonResponse
    
    try:
        # Получаем параметры фильтров
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        region = request.GET.get('region', '')
        product = request.GET.get('product', '')
        source = request.GET.get('source', '')
        
        # Парсим даты
        tz = timezone.get_current_timezone()
        start_date = timezone.make_aware(datetime.strptime(date_from, '%Y-%m-%d'), tz)
        end_date = timezone.make_aware(datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59), tz)
        
        # Базовый queryset
        qs = ContactForm.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Применяем фильтры
        if region:
            qs = qs.filter(region=region)
        if product:
            qs = qs.filter(product__icontains=product)
        if source:
            # Фильтр по источнику через utm_data
            if source == 'direct':
                qs = qs.filter(Q(utm_data__isnull=True) | Q(utm_data=''))
            else:
                qs = qs.filter(utm_data__icontains=f'"utm_source":"{source}"')
        
        # Вызываем функции из services/dashboard
        from main.services.dashboard.analytics import calculate_kpi
        from main.services.dashboard.charts import get_chart_data
        
        kpi = calculate_kpi(qs, start_date, end_date)
        charts = get_chart_data(qs, start_date, end_date)
        
        return JsonResponse({
            'success': True,
            'kpi': kpi,
            'charts': charts,
        })
        
    except Exception as e:
        logger.error(f"Ошибка dashboard API: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@staff_member_required
def dashboard_export_excel(request):
    """Экспорт dashboard в Excel"""
    # TODO: Реализуем на следующем шаге
    pass


@staff_member_required
def dashboard_export_word(request):
    """Экспорт dashboard в Word"""
    # TODO: Реализуем на следующем шаге
    pass

class PromotionViewSet(viewsets.ReadOnlyModelViewSet):
    """API для получения активных акций"""
    serializer_class = PromotionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        now = timezone.now()
        return Promotion.objects.filter(
            is_active=True,
            show_on_homepage=True,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).order_by('-priority', '-created_at')