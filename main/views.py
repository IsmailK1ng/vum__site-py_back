# main/views.py

from django.conf import settings
from django.shortcuts import render, redirect
from django.utils import translation
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .models import (
    News, ContactForm, JobApplication, Vacancy, Product,
    Dealer, DealerService, BecomeADealerPage, BecomeADealerApplication
)
from .serializers import (
    NewsSerializer, ContactFormSerializer, JobApplicationSerializer, 
    ProductCardSerializer, ProductDetailSerializer,
    DealerSerializer, DealerServiceSerializer, 
    BecomeADealerPageSerializer, BecomeADealerApplicationSerializer
)
import json
import logging

logger = logging.getLogger('amocrm')

# === FRONTEND views === 
def index(request):
    """Главная страница с динамическим слайдером"""
    
    # Получаем текущий язык
    from django.utils.translation import get_language
    current_lang = get_language()
    
    # Получить 8 последних активных новостей для слайдера
    news_list = News.objects.filter(
        is_active=True
    ).select_related('author').order_by('-order', '-created_at')[:8]
    
    # Получаем продукты для главного слайдера
    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    ).order_by('-slider_order', '-created_at')[:10]  # Максимум 10 слайдов
    
    # Формируем данные для слайдера с учетом языка
    slider_data = []
    for product in featured_products:
        # Получаем переведенные поля
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
        
        # Приоритет изображений: slider_image > main_image
        if product.slider_image:
            slider_item['image'] = product.slider_image.url
        elif product.main_image:
            slider_item['image'] = product.main_image.url
        
        slider_data.append(slider_item)
    
    context = {
        'news_list': news_list,
        'slider_products': json.dumps(slider_data, ensure_ascii=False),
        'featured_count': len(slider_data),  # Для отладки
    }
    
    return render(request, 'main/index.html', context)

def about(request):
    return render(request, 'main/about.html')

def contact(request):
    return render(request, 'main/contact.html')

def services(request):
    return render(request, 'main/services.html')

def product_detail(request, product_id):
    return render(request, 'main/product_detail.html', {'product_id': product_id})

def become_a_dealer(request):
    page_data = BecomeADealerPage.get_instance()
    
    context = {
        'page_data': page_data,
        'requirements': page_data.requirements.all().order_by('order')
    }
    return render(request, 'main/become_a_dealer.html', context)

def lizing(request):
    return render(request, 'main/lizing.html')

def news(request):
    """Страница со всеми новостями"""
    news_list = News.objects.filter(is_active=True).select_related('author').order_by('-order', '-created_at')
    
    return render(request, 'main/news.html', {
        'news_list': news_list
    })

def dealers(request):
    return render(request, 'main/dealers.html')

def jobs(request):
    """Страница с вакансиями"""
    vacancies = Vacancy.objects.filter(is_active=True).prefetch_related(
        'responsibilities', 
        'requirements', 
        'ideal_candidates',
        'conditions'
    ).order_by('order', '-created_at')
    
    return render(request, 'main/jobs.html', {'vacancies': vacancies})


def news_detail(request, slug):
    """Детальная страница новости"""
    news = get_object_or_404(News.objects.prefetch_related('blocks'), slug=slug, is_active=True)
    
    # Хлебные крошки на 3 языках
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


def set_language_get(request):
    """Переключение языка через GET или POST"""
    from django.http import HttpResponseRedirect
    
    lang = request.GET.get("language") or request.POST.get("language")
    
    supported_languages = [code for code, name in settings.LANGUAGES]
    
    if lang and lang in supported_languages:
        translation.activate(lang)
        request.session[translation.LANGUAGE_SESSION_KEY] = lang
        
        response = HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path='/',
        )
        return response
    
    return redirect(request.META.get("HTTP_REFERER", "/"))


# === API ViewSets ===
class NewsViewSet(viewsets.ModelViewSet):
    """API endpoint для CRUD операций с новостями"""
    queryset = News.objects.all().order_by('-created_at')
    serializer_class = NewsSerializer
    permission_classes = [AllowAny]


class ContactFormViewSet(viewsets.ModelViewSet):
    """
    API для контактных форм FAW.UZ
    """
    serializer_class = ContactFormSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'region', 'amocrm_status'] 
    search_fields = ['name', 'phone']
    ordering_fields = ['created_at', 'priority']
    
    def get_queryset(self):
        queryset = ContactForm.objects.all().order_by('-created_at')
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset
    
    def create(self, request, *args, **kwargs):
        # ============ БЛОК 5: ЛОГ ЗАПРОСА ============
        logger.info(f"🌐 === ВХОДЯЩИЙ ЗАПРОС ===")
        logger.info(f"📍 IP: {request.META.get('REMOTE_ADDR')}")
        logger.info(f"🔗 Referer: {request.META.get('HTTP_REFERER')}")
        logger.info(f"📦 Body: {str(request.data)[:500]}")  # ← ИСПРАВЛЕНО!
        logger.info(f"🎯 Query params: {request.GET.dict()}")
        # ============ КОНЕЦ БЛОКА 5 ============
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            contact_form = serializer.save()
            
            try:
                from main.services.amocrm.lead_sender import LeadSender
                LeadSender.send_lead(contact_form)
                contact_form.refresh_from_db()
                
                if contact_form.amocrm_status == 'sent':
                    logger.info(f"Лид #{contact_form.id} успешно отправлен в amoCRM")
                else:
                    logger.warning(f"Лид #{contact_form.id} не отправлен: {contact_form.amocrm_error}")
                    
            except Exception as amocrm_error:
                logger.error(f"Ошибка amoCRM для лида #{contact_form.id}: {str(amocrm_error)}")
            
            return Response({
                'success': True,
                'message': 'Xabar yuborildi!'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Критическая ошибка создания формы: {str(e)}")
            return Response({
                'success': False,
                'message': 'Xatolik yuz berdi.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика по заявкам"""
        total = ContactForm.objects.count()
        new = ContactForm.objects.filter(status='new').count()
        in_process = ContactForm.objects.filter(status='in_process').count()
        done = ContactForm.objects.filter(status='done').count()
        
        amocrm_sent = ContactForm.objects.filter(amocrm_status='sent').count()
        amocrm_failed = ContactForm.objects.filter(amocrm_status='failed').count()
        amocrm_pending = ContactForm.objects.filter(amocrm_status='pending').count()
        
        return Response({
            'total': total,
            'new': new,
            'in_process': in_process,
            'done': done,
            'amocrm': {
                'sent': amocrm_sent,
                'failed': amocrm_failed,
                'pending': amocrm_pending
            }
        })

class JobApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint для приема заявок на вакансии"""
    queryset = JobApplication.objects.all().order_by('-created_at')
    serializer_class = JobApplicationSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        else:
            return [IsAdminUser()]
    
    def create(self, request, *args, **kwargs):
        """Создание новой заявки с резюме"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            {
                'success': True,
                'message': 'Rezyume muvaffaqiyatli yuborildi! Tez orada siz bilan bog\'lanamiz.',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def unprocessed(self, request):
        """Получить необработанные заявки"""
        unprocessed = self.queryset.filter(is_processed=False)
        serializer = self.get_serializer(unprocessed, many=True)
        return Response({
            'count': unprocessed.count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_processed(self, request, pk=None):
        """Отметить заявку как обработанную"""
        application = self.get_object()
        application.is_processed = True
        application.save()
        return Response({
            'status': 'processed',
            'message': f'Ariza #{application.id} ko\'rib chiqilgan deb belgilandi'
        })


# ========== API ДЛЯ ПРОДУКТОВ ==========
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для продуктов FAW
    """
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).prefetch_related(
            'card_specs__icon',
            'parameters',
            'features__icon',
            'gallery'
        ).order_by('order', 'title')
        
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductCardSerializer


# ========== СТРАНИЦЫ С КАТЕГОРИЯМИ ==========
def products(request):
    """Страница со списком продуктов по категориям"""
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
# API для дилеров

class DealerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Dealer.objects.filter(is_active=True).prefetch_related('services').order_by('order', 'city')
    serializer_class = DealerSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['city', 'services__slug']
    search_fields = ['name', 'city', 'address']


class DealerServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DealerService.objects.filter(is_active=True).order_by('order')
    serializer_class = DealerServiceSerializer
    permission_classes = [AllowAny]


class BecomeADealerPageViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    def list(self, request):
        page = BecomeADealerPage.get_instance()
        serializer = BecomeADealerPageSerializer(page)
        return Response(serializer.data)


class BecomeADealerApplicationViewSet(viewsets.ModelViewSet):
    queryset = BecomeADealerApplication.objects.all().order_by('-created_at')
    serializer_class = BecomeADealerApplicationSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': "Arizangiz qabul qilindi! Tez orada siz bilan bog'lanamiz."
        }, status=status.HTTP_201_CREATED)