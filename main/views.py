from django.conf import settings
from django.shortcuts import render, redirect
from django.utils import translation
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from .models import News, ContactForm, JobApplication, Vacancy
from .serializers import NewsSerializer, ContactFormSerializer, JobApplicationSerializer


# === FRONTEND views === 
def index(request):
    return render(request, 'main/index.html')

def about(request):
    return render(request, 'main/about.html')

def contact(request):
    return render(request, 'main/contact.html')

def services(request):
    return render(request, 'main/services.html')

def products(request):
    return render(request, 'main/products.html')

def product_detail(request, product_id):
    return render(request, 'main/product_detail.html', {'product_id': product_id})

def become_a_dealer(request):
    return render(request, 'main/become_a_dealer.html')

def lizing(request):
    return render(request, 'main/lizing.html')

def news(request):
    return render(request, 'main/news.html')

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

def new_detail(request, new_id):
    return render(request, 'main/news_detail.html', {'new_id': new_id})


# === LANGUAGE SWITCH ===
def set_language_get(request):
    lang = request.GET.get("language")
    if lang in dict(settings.LANGUAGES):
        translation.activate(lang)
        request.session[translation.LANGUAGE_SESSION_KEY] = lang
    return redirect(request.META.get("HTTP_REFERER", "/"))


# === API ViewSets ===
class NewsViewSet(viewsets.ModelViewSet):
    """API endpoint для CRUD операций с новостями"""
    queryset = News.objects.all().order_by('-created_at')
    serializer_class = NewsSerializer
    permission_classes = [AllowAny]


class ContactFormViewSet(viewsets.ModelViewSet):
    """API endpoint для приема контактных форм"""
    queryset = ContactForm.objects.all().order_by('-created_at')
    serializer_class = ContactFormSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        else:
            return [IsAdminUser()]
    
    def create(self, request):
        """Создание новой заявки с контактной формы"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact_form = serializer.save()
        
        return Response(
            {
                'success': True,
                'message': 'Xabaringiz qabul qilindi. Tez orada siz bilan bog\'lanamiz.',
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
        contact_form = self.get_object()
        contact_form.is_processed = True
        contact_form.save()
        return Response({
            'status': 'processed',
            'message': f'Ariza #{contact_form.id} ko\'rib chiqilgan deb belgilandi'
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def statistics(self, request):
        """Получить статистику по заявкам"""
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        total = self.queryset.count()
        processed = self.queryset.filter(is_processed=True).count()
        unprocessed = self.queryset.filter(is_processed=False).count()
        today = self.queryset.filter(
            created_at__date=datetime.now().date()
        ).count()
        this_week = self.queryset.filter(
            created_at__gte=datetime.now() - timedelta(days=7)
        ).count()
        
        by_region = self.queryset.values('region').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total': total,
            'processed': processed,
            'unprocessed': unprocessed,
            'today': today,
            'this_week': this_week,
            'by_region': by_region
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