from django.conf import settings
from django.shortcuts import render, redirect
from django.utils import translation
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.core.mail import send_mail
from .models import News, ContactForm  # Добавили ContactForm
from .serializers import NewsSerializer, ContactFormSerializer  # Добавили ContactFormSerializer


# === FRONTEND views === 
# (ваши существующие view функции остаются без изменений)
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
    return render(request, 'main/jobs.html')

def new_detail(request, new_id):
    return render(request, 'main/news_detail.html', {'new_id': new_id})


# === LANGUAGE SWITCH ===
def set_language_get(request):
    lang = request.GET.get("language")
    if lang in dict(settings.LANGUAGES):
        translation.activate(lang)
        request.session[translation.LANGUAGE_SESSION_KEY] = lang
    return redirect(request.META.get("HTTP_REFERER", "/"))


# === API views ===
class NewsViewSet(viewsets.ModelViewSet):
    """API endpoint для CRUD операций с новостями"""
    queryset = News.objects.all().order_by('-created_at')
    serializer_class = NewsSerializer
    permission_classes = [AllowAny]  # Новости доступны всем


class ContactFormViewSet(viewsets.ModelViewSet):
    """API endpoint для приема контактных форм"""
    queryset = ContactForm.objects.all().order_by('-created_at')
    serializer_class = ContactFormSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            # Любой может отправить форму
            return [AllowAny()]
        else:
            # Только админы могут просматривать/изменять
            return [IsAdminUser()]
    
    def create(self, request):
        """Создание новой заявки с контактной формы"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact_form = serializer.save()
        
        # Опционально: отправка email уведомления
        # try:
        #     self.send_notification_email(contact_form)
        # except Exception as e:
        #     print(f"Email sending failed: {e}")
        
        return Response(
            {
                'success': True,
                'message': 'Xabaringiz qabul qilindi. Tez orada siz bilan bog\'lanamiz.',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def send_notification_email(self, contact_form):
        """Отправка email уведомления администратору (опционально)"""
        subject = f'Yangi kontakt forma - {contact_form.name}'
        message = f"""
        Yangi kontakt forma yuborildi:
        
        Ism: {contact_form.name}
        Viloyat: {contact_form.region}
        Telefon: {contact_form.phone}
        Xabar: {contact_form.message}
        
        Yuborilgan vaqt: {contact_form.created_at.strftime('%d.%m.%Y %H:%M')}
        
        Admin panelda ko'rish: http://yourdomain.com/admin/main/contactform/{contact_form.id}/
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['info@fawtrucks.uz'],  # или получить из settings
            fail_silently=False,
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