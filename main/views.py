# main/views.py

# ========== СТАНДАРТНАЯ БИБЛИОТЕКА ==========
import json
import logging
from datetime import datetime, timedelta

# ========== DJANGO CORE ==========
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncHour, TruncDate
from django.http import HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import translation, timezone

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
    REGION_CHOICES
)
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
            power = getattr(product, f'slider_power_{current_lang}', None) or product.slider_power or '—'
            fuel = getattr(product, f'slider_fuel_consumption_{current_lang}', None) or product.slider_fuel_consumption or '—'
            
            slider_item = {
                'year': product.slider_year,
                'title': title,
                'price': price,
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
    return render(request, 'main/about.html')


def contact(request):
    return render(request, 'main/contact.html')


def services(request):
    return render(request, 'main/services.html')


def product_detail(request, product_id):
    return render(request, 'main/product_detail.html', {'product_id': product_id})


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
        
        vacancies = Vacancy.objects.filter(is_active=True).prefetch_related(
            'responsibilities', 
            'requirements', 
            'ideal_candidates',
            'conditions'
        ).order_by('order', '-created_at')
        
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


def set_language_get(request):
    """Переключение языка ТОЛЬКО для сайта"""
    language = request.GET.get('language') or request.POST.get('language')
    
    if language and language in ['uz', 'ru', 'en']:
        request.session['_language'] = language
        next_url = request.META.get('HTTP_REFERER', '/')
        
        response = redirect(next_url)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language,
            max_age=365*24*60*60,
            path='/',
            samesite='Lax'
        )
        return response
    
    return redirect('/')


# === API ViewSets ===

class NewsViewSet(viewsets.ModelViewSet):
    """API endpoint для CRUD операций с новостями"""
    serializer_class = NewsSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return News.objects.select_related('author').prefetch_related('blocks').order_by('-created_at')


class ContactFormViewSet(viewsets.ModelViewSet):
    """API для контактных форм FAW.UZ"""
    serializer_class = ContactFormSerializer
    
    # ✅ ИСПРАВЛЕНО: Разные права для разных методов
    def get_permissions(self):
        if self.action in ['create']:
            # POST требует CSRF в headers
            return [AllowAny()]
        else:
            # GET/PUT/DELETE только для админов
            return [IsAdminUser()]
    
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
                    logger.warning(
                        f"🚫 reCAPTCHA failed for contact form: score={score}, error={recaptcha_result['error']}"
                    )
                    return Response({
                        'success': False,
                        'message': 'Подозрительная активность. Попробуйте позже.',
                        'errors': {'recaptcha': recaptcha_result['error']}
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
        
        return render(request, 'main/products.html', {
            'category': category,
            'category_info': category_info
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