# main/services/dashboard/insights.py

from django.db.models import Count, Q, Avg
from django.db.models.functions import ExtractHour, ExtractWeekDay
import json


def generate_insights(queryset, start_date, end_date):
    """
    Генерирует автоматические инсайты и рекомендации
    
    Returns:
        dict: {
            'good': [...],           # Что работает хорошо
            'problems': [...],       # Проблемы и возможности
            'recommendations': [...]  # Рекомендации
        }
    """
    
    good = []
    problems = []
    recommendations = []
    
    total_leads = queryset.count()
    
    if total_leads == 0:
        return {
            'good': ['Нет данных за выбранный период'],
            'problems': [],
            'recommendations': []
        }
    
    # 1. Анализ дней недели
    _analyze_weekdays(queryset, total_leads, good, problems, recommendations)
    
    # 2. Анализ часов суток
    _analyze_hours(queryset, total_leads, good, problems, recommendations)
    
    # 3. Анализ источников
    _analyze_sources(queryset, total_leads, good, problems, recommendations)
    
    # 4. Анализ моделей
    _analyze_models(queryset, total_leads, good, problems, recommendations)
    
    # 5. Анализ регионов
    _analyze_regions(queryset, total_leads, good, problems, recommendations)
    
    return {
        'good': good,
        'problems': problems,
        'recommendations': recommendations
    }


def _analyze_weekdays(queryset, total_leads, good, problems, recommendations):
    """Анализ дней недели"""
    
    weekday_names = {0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг', 4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'}
    
    weekdays = queryset.annotate(
        weekday=ExtractWeekDay('created_at')
    ).values('weekday').annotate(
        count=Count('id')
    ).order_by('-count')
    
    if weekdays:
        # Лучший день
        best = weekdays[0]
        best_day = weekday_names.get(best['weekday'] - 1, 'Неизвестно')
        best_percent = round(best['count'] / total_leads * 100, 0)
        good.append(f"{best_day} — самый продуктивный день ({best['count']} заявок, {best_percent}%)")
        
        # Худший день
        worst = weekdays[len(weekdays) - 1]
        worst_day = weekday_names.get(worst['weekday'] - 1, 'Неизвестно')
        worst_percent = round(worst['count'] / total_leads * 100, 0)
        
        avg_per_day = total_leads / 7
        if worst['count'] < avg_per_day * 0.5:
            problems.append(f"{worst_day} — всего {worst['count']} заявок ({worst_percent}%), снизить бюджет")
            recommendations.append(f"Снизить ставки рекламы в {worst_day.lower()}")


def _analyze_hours(queryset, total_leads, good, problems, recommendations):
    """Анализ часов суток"""
    
    hours = queryset.annotate(
        hour=ExtractHour('created_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-count')
    
    if hours:
        # Пиковый час
        peak = hours[0]
        good.append(f"{peak['hour']:02d}:00-{peak['hour']+1:02d}:00 — пиковый час ({peak['count']} заявок)")
        recommendations.append(f"Увеличить бюджет рекламы в {peak['hour']:02d}:00-{peak['hour']+1:02d}:00")
        
        # Ночные часы (00-06)
        night_leads = queryset.filter(created_at__hour__gte=0, created_at__hour__lt=6).count()
        night_percent = round(night_leads / total_leads * 100, 1)
        
        if night_percent < 3:
            problems.append(f"Ночное время (00-06) — только {night_percent}% заявок")
            recommendations.append("Рассмотреть отключение рекламы ночью для экономии бюджета")


def _analyze_sources(queryset, total_leads, good, problems, recommendations):
    """Анализ источников трафика"""
    
    sources = {
        'google': {'count': 0, 'amocrm': 0},
        'instagram': {'count': 0, 'amocrm': 0},
        'facebook': {'count': 0, 'amocrm': 0},
    }
    
    for lead in queryset:
        if lead.utm_data:
            try:
                utm = json.loads(lead.utm_data)
                source = utm.get('utm_source', '').lower()
                
                key = None
                if 'google' in source:
                    key = 'google'
                elif 'instagram' in source or 'ig' in source:
                    key = 'instagram'
                elif 'facebook' in source or 'fb' in source:
                    key = 'facebook'
                
                if key:
                    sources[key]['count'] += 1
                    if lead.amocrm_status == 'sent':
                        sources[key]['amocrm'] += 1
            except:
                pass
    
    # Анализируем каждый источник
    for source, data in sources.items():
        if data['count'] > 0:
            conversion = round(data['amocrm'] / data['count'] * 100, 1)
            percent = round(data['count'] / total_leads * 100, 1)
            
            source_name = {'google': 'Google Ads', 'instagram': 'Instagram', 'facebook': 'Facebook'}.get(source, source)
            
            if conversion >= 90:
                good.append(f"{source_name} — отличная конверсия {conversion}%")
                recommendations.append(f"Масштабировать {source_name} (+20-30% бюджета)")
            elif conversion < 80:
                problems.append(f"{source_name} — низкая конверсия {conversion}% (ниже среднего)")
                recommendations.append(f"Оптимизировать креативы и таргетинг для {source_name}")


def _analyze_models(queryset, total_leads, good, problems, recommendations):
    """Анализ моделей"""
    
    top_model = queryset.exclude(
        Q(product__isnull=True) | Q(product='')
    ).values('product').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    if top_model:
        percent = round(top_model['count'] / total_leads * 100, 1)
        good.append(f"{top_model['product']} — самая популярная модель ({top_model['count']} заявок, {percent}%)")
        recommendations.append(f"Запустить дополнительную кампанию для {top_model['product']}")


def _analyze_regions(queryset, total_leads, good, problems, recommendations):
    """Анализ регионов"""
    
    from main.models import REGION_CHOICES
    region_dict = dict(REGION_CHOICES)
    
    top_region = queryset.values('region').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    if top_region:
        region_name = region_dict.get(top_region['region'], top_region['region']).replace(' viloyati', '').replace(' shahri', '')
        percent = round(top_region['count'] / total_leads * 100, 1)
        good.append(f"{region_name} — основной рынок ({percent}% всех заявок)")
        
        # Если один регион доминирует
        if percent > 50:
            problems.append(f"Высокая зависимость от {region_name} ({percent}%)")
            recommendations.append("Усилить маркетинг в других регионах для диверсификации")