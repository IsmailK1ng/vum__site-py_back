from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, BasePermission
from datetime import datetime
from django.http import HttpResponse, Http404
from django.db import models
from django.shortcuts import get_object_or_404, render
from django.contrib.admin.views.decorators import staff_member_required
from .models import KGVehicle, KGFeedback, KGHeroSlide
from .serializers import (
    KGVehicleListSerializer,
    KGVehicleDetailSerializer,
    KGFeedbackSerializer,
    KGFeedbackCreateSerializer,
    KGHeroSlideSerializer
)

# ============================================
# CUSTOM PERMISSIONS
# ============================================

class IsSuperUser(BasePermission):
    """Доступ только для суперпользователей"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

# ============================================
# VIEWSET: МАШИНЫ (КАТАЛОГ)
# ============================================

class KGVehicleViewSet(viewsets.ReadOnlyModelViewSet):
    """API для машин FAW.KG"""
    queryset = KGVehicle.objects.filter(is_active=True).select_related().prefetch_related(
        'mini_images',
        'card_specs'
    )
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_object(self):
        """
        Ищем машину по любому из slug (ru/ky/en)
        """
        lookup_value = self.kwargs.get(self.lookup_field)
        
        queryset = self.get_queryset()
        obj = queryset.filter(
            models.Q(slug=lookup_value) |
            models.Q(slug_ru=lookup_value) |
            models.Q(slug_ky=lookup_value) |
            models.Q(slug_en=lookup_value)
        ).first()
        
        if not obj:
            raise Http404(f"Машина с slug '{lookup_value}' не найдена")
        
        return obj
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return KGVehicleDetailSerializer
        return KGVehicleListSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['lang'] = self.request.query_params.get('lang', 'ru')
        return context


# ============================================
# VIEWSET: ЗАЯВКИ
# ============================================

class KGFeedbackViewSet(viewsets.ModelViewSet):
    """API для заявок с сайта faw.kg"""
    queryset = KGFeedback.objects.all().select_related('vehicle').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return KGFeedbackCreateSerializer
        return KGFeedbackSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def create(self, request):
        """Создание новой заявки"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save()
        
        return Response(
            {
                'success': True,
                'message': 'Ваша заявка принята. Мы свяжемся с вами в ближайшее время.',
                'data': KGFeedbackSerializer(feedback).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsSuperUser])
    def statistics(self, request):
        """Статистика с фильтрами"""
        from datetime import timedelta
        from django.db.models import Count
        from django.utils import timezone
        
        # ============ ФИЛЬТРЫ ============
        queryset = self.queryset
        
        # Фильтр по датам
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Фильтр по региону
        region = request.query_params.get('region')
        if region:
            queryset = queryset.filter(region=region)
        
        # ============ СТАТИСТИКА ============
        # По статусам
        new = queryset.filter(status='new').count()
        in_process = queryset.filter(status='in_process').count()
        processed = queryset.filter(status='done').count()
        
        # Временные периоды
        now = timezone.now()
        today = queryset.filter(created_at__date=now.date()).count()
        this_week = queryset.filter(created_at__gte=now - timedelta(days=7)).count()
        this_month = queryset.filter(
            created_at__month=now.month,
            created_at__year=now.year
        ).count()
        
        # По регионам
        by_region = queryset.values('region').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # По машинам
        by_vehicle = queryset.filter(vehicle__isnull=False).values(
            'vehicle__id', 'vehicle__title_ru'
        ).annotate(count=Count('id')).order_by('-count')[:5]
        
        # По менеджерам
        by_manager = queryset.filter(manager__isnull=False).values(
            'manager__id', 'manager__username'
        ).annotate(count=Count('id')).order_by('-count')
        
        # По приоритетам
        by_priority = queryset.values('priority').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Список заявок для таблицы
        feedbacks_list = queryset.select_related('vehicle', 'manager').values(
            'id',
            'name',
            'phone',
            'region',
            'vehicle__title_ru',
            'status',
            'priority',
            'manager__username',
            'created_at'
        ).order_by('-created_at')[:100]
        
        return Response({
            'by_status': {
                'new': new,
                'in_process': in_process,
                'processed': processed
            },
            'time_periods': {
                'today': today,
                'this_week': this_week,
                'this_month': this_month
            },
            'by_region': list(by_region),
            'by_vehicle': list(by_vehicle),
            'by_manager': list(by_manager),
            'by_priority': list(by_priority),
            'feedbacks_list': list(feedbacks_list)
        })


# ============================================
# VIEWSET: HERO-СЛАЙДЫ
# ============================================

class KGHeroSlideViewSet(viewsets.ReadOnlyModelViewSet):
    """API для Hero-слайдов"""
    queryset = KGHeroSlide.objects.filter(is_active=True).select_related('vehicle')
    serializer_class = KGHeroSlideSerializer
    permission_classes = [AllowAny]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['lang'] = self.request.query_params.get('lang', 'ru')
        return context


# ============================================
# VIEWSET: БЫСТРОЕ ОБНОВЛЕНИЕ ЗАЯВОК
# ============================================

class KGFeedbackQuickUpdateViewSet(viewsets.ViewSet):
    """
    Быстрое обновление полей заявки (для автосохранения в админке)
    Endpoint: PATCH /api/kg/feedback-update/{id}/quick-update/
    """
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['patch'], url_path='quick-update')
    def quick_update(self, request, pk=None):
        feedback = get_object_or_404(KGFeedback, pk=pk)
        
        allowed_fields = ['status', 'priority', 'manager']
        
        updated_fields = []
        for field in allowed_fields:
            if field in request.data:
                if field == 'manager':
                    manager_id = request.data[field]
                    if manager_id and manager_id != '':
                        feedback.manager_id = manager_id
                        updated_fields.append('manager')
                    elif manager_id == '':
                        feedback.manager = None
                        updated_fields.append('manager')
                else:
                    setattr(feedback, field, request.data[field])
                    updated_fields.append(field)
        
        if updated_fields:
            feedback.save(update_fields=updated_fields)
            return Response({
                'success': True,
                'message': f'Обновлено: {", ".join(updated_fields)}',
                'data': {
                    'status': feedback.status,
                    'priority': feedback.priority,
                    'manager': feedback.manager_id if feedback.manager else None
                }
            })
        
        return Response({
            'success': False,
            'message': 'Нет полей для обновления'
        }, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# СТРАНИЦА СТАТИСТИКИ ДЛЯ АДМИНКИ
# ============================================

@staff_member_required
def kg_stats_dashboard(request):
    if not request.user.is_superuser:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden(
            '<h1 style="text-align:center; margin-top:100px; color:#dc3545;">'
            '🚫 Доступ запрещён<br><small>Только для суперпользователей</small>'
            '</h1>'
        )
    
    return render(request, 'admin/kg_dashboard.html', {
        'title': 'Статистика FAW.KG',
        'site_header': 'Статистика заявок',
    })