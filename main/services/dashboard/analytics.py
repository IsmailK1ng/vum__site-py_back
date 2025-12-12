# main/services/dashboard/analytics.py

from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta
import json


def calculate_kpi(queryset, start_date, end_date):
    """
    Рассчитывает основные KPI метрики
    
    Returns:
        dict: {
            'total_leads': int,
            'amocrm_conversion': float,
            'avg_response_time': int (минуты),
            'trend': dict
        }
    """
    
    # 1. Всего заявок
    total_leads = queryset.count()
    
    # 2. Конверсия в amoCRM
    amocrm_sent = queryset.filter(amocrm_status='sent').count()
    amocrm_conversion = round((amocrm_sent / total_leads * 100), 1) if total_leads > 0 else 0
    
    # 3. Среднее время обработки (пока заглушка, можно добавить реальный расчёт)
    avg_response_time = 11  # минут
    
    # 4. Тренд к предыдущему периоду
    period_days = (end_date - start_date).days + 1
    prev_start = start_date - timedelta(days=period_days)
    prev_end = start_date - timedelta(days=1)
    
    prev_leads = queryset.model.objects.filter(
        created_at__gte=prev_start,
        created_at__lte=prev_end
    ).count()
    
    if prev_leads > 0:
        trend_value = round(((total_leads - prev_leads) / prev_leads * 100), 1)
        trend_direction = 'up' if trend_value > 0 else 'down' if trend_value < 0 else 'equal'
    else:
        trend_value = 0
        trend_direction = 'equal'
    
    return {
        'total_leads': total_leads,
        'amocrm_sent': amocrm_sent,
        'amocrm_conversion': amocrm_conversion,
        'avg_response_time': avg_response_time,
        'trend': {
            'value': trend_value,
            'direction': trend_direction,
            'prev_period': prev_leads
        }
    }