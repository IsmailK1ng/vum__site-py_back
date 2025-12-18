# main/services/dashboard/charts.py

from django.db.models import Count, Q
from django.db.models.functions import TruncDate, ExtractHour, ExtractWeekDay
from datetime import datetime, timedelta
from django.utils import timezone as django_tz
import json


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def _get_source_from_utm(lead):
    """
    Определяет источник трафика из UTM данных ИЛИ REFERER
    """
    # 1. ПРОВЕРЯЕМ UTM (ПРИОРИТЕТ)
    if lead.utm_data and lead.utm_data != '':
        try:
            utm = json.loads(lead.utm_data)
            source = utm.get('utm_source', '').lower()
            
            if 'google' in source:
                return 'google'
            elif source in ['ig', 'instagram']:
                return 'instagram'
            elif source in ['fb', 'facebook']:
                return 'facebook'
            elif 'yandex' in source or source == 'yd':
                return 'yandex'
            elif 'telegram' in source or source == 'tg':
                return 'telegram'
            elif 'tiktok' in source or source == 'tt':
                return 'tiktok'
            elif 'youtube' in source or source == 'yt':
                return 'youtube'
            else:
                return 'other'
        except:
            pass  # Если ошибка парсинга — проверяем referer
    
    # 2. ПРОВЕРЯЕМ REFERER (ЕСЛИ НЕТ UTM)
    if lead.referer and lead.referer != '':
        referer_lower = lead.referer.lower()
        
        if 'facebook.com' in referer_lower or 'm.facebook.com' in referer_lower:
            return 'facebook'
        elif 'instagram.com' in referer_lower:
            return 'instagram'
        elif 'google.com' in referer_lower or 'google.' in referer_lower:
            return 'google'
        elif 'yandex' in referer_lower:
            return 'yandex'
        elif 'telegram' in referer_lower or 't.me' in referer_lower:
            return 'telegram'
        elif 'tiktok.com' in referer_lower:
            return 'tiktok'
        elif 'youtube.com' in referer_lower or 'youtu.be' in referer_lower:
            return 'youtube'
        else:
            return 'other'
    
    # 3. НИ UTM, НИ REFERER — ПРЯМОЙ ЗАХОД
    return 'direct'


# ========== ГЛАВНАЯ ФУНКЦИЯ ==========

def get_chart_data(queryset, start_date, end_date):
    """
    Подготавливает данные для всех графиков
    """
    
    dynamics = _get_dynamics_data(queryset, start_date, end_date)
    sources = _get_sources_data(queryset)
    top_models = _get_top_models(queryset)
    top_regions = _get_top_regions(queryset)
    heatmap = _get_heatmap_data(queryset)
    time_analysis = get_time_analysis(queryset)
    utm_campaigns = get_utm_campaigns(queryset)
    referer_data = _get_referer_data(queryset)  
    region_model_matrix = get_region_model_matrix(queryset)
    source_model_matrix = get_source_model_matrix(queryset)
    behavior = get_behavior_data(queryset)
    
    return {
        'dynamics': dynamics,
        'sources': sources,
        'top_models': top_models,
        'top_regions': top_regions,
        'heatmap': heatmap,
        'time_analysis': time_analysis,
        'utm_campaigns': utm_campaigns,
        'referer_data': referer_data,
        'region_model_matrix': region_model_matrix,
        'source_model_matrix': source_model_matrix,
        'behavior': behavior,
    }


# ========== ГРАФИКИ ==========

def _get_dynamics_data(queryset, start_date, end_date):
    """Динамика заявок по дням с сравнением"""
    
    current_data = queryset.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    labels = []
    values = []
    
    for item in current_data:
        labels.append(item['date'].strftime('%d.%m'))
        values.append(item['count'])
    
    # Предыдущий период
    period_days = (end_date - start_date).days + 1
    prev_start = start_date - timedelta(days=period_days)
    prev_end = start_date - timedelta(days=1)
    
    prev_data = queryset.model.objects.filter(
        created_at__gte=prev_start,
        created_at__lte=prev_end
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    prev_values = [item['count'] for item in prev_data]
    
    return {
        'labels': labels,
        'current': values,
        'previous': prev_values,
    }


def _get_sources_data(queryset):
    """Распределение по источникам трафика"""
    
    sources = {
        'google': 0,
        'yandex': 0,
        'instagram': 0,
        'facebook': 0,
        'telegram': 0,
        'tiktok': 0,
        'youtube': 0,
        'direct': 0,
        'other': 0
    }
    

    for lead in queryset:
        source_key = _get_source_from_utm(lead)
        sources[source_key] += 1

    total = sum(sources.values())

    return {
        'labels': ['Google', 'Яндекс', 'Instagram', 'Facebook', 'Telegram', 'TikTok', 'YouTube', 'Прямые', 'Другие'],
        'values': [
            sources['google'],
            sources['yandex'],
            sources['instagram'],
            sources['facebook'],
            sources['telegram'],
            sources['tiktok'],
            sources['youtube'],
            sources['direct'],
            sources['other']
        ],
        'percentages': [
            round(sources['google'] / total * 100, 1) if total > 0 else 0,
            round(sources['yandex'] / total * 100, 1) if total > 0 else 0,
            round(sources['instagram'] / total * 100, 1) if total > 0 else 0,
            round(sources['facebook'] / total * 100, 1) if total > 0 else 0,
            round(sources['telegram'] / total * 100, 1) if total > 0 else 0,
            round(sources['tiktok'] / total * 100, 1) if total > 0 else 0,
            round(sources['youtube'] / total * 100, 1) if total > 0 else 0,
            round(sources['direct'] / total * 100, 1) if total > 0 else 0,
            round(sources['other'] / total * 100, 1) if total > 0 else 0,
        ]
    }
    
def _get_top_models(queryset):
    """Топ-10 популярных моделей"""
    
    models = queryset.exclude(
        Q(product__isnull=True) | Q(product='')
    ).values('product').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    total = queryset.count()
    
    return {
        'labels': [item['product'] for item in models],
        'values': [item['count'] for item in models],
        'percentages': [
            round(item['count'] / total * 100, 1) if total > 0 else 0
            for item in models
        ]
    }


def _get_top_regions(queryset):
    """Топ-5 регионов"""
    
    regions = queryset.values('region').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    total = queryset.count()
    
    from main.models import REGION_CHOICES
    region_dict = dict(REGION_CHOICES)
    
    return {
        'labels': [
            region_dict.get(item['region'], item['region']).replace(' viloyati', '').replace(' shahri', '')
            for item in regions
        ],
        'values': [item['count'] for item in regions],
        'percentages': [
            round(item['count'] / total * 100, 1) if total > 0 else 0
            for item in regions
        ]
    }


def _get_heatmap_data(queryset):
    """Тепловая карта: час × день недели"""
    
    heatmap = [[0 for _ in range(24)] for _ in range(7)]
    
    for lead in queryset:
        # Конвертируем UTC в локальное время
        local_time = lead.created_at.astimezone(django_tz.get_current_timezone())
        hour = local_time.hour  
        weekday = local_time.weekday()
        heatmap[weekday][hour] += 1  
    
    max_value = max(max(row) for row in heatmap) if heatmap else 1
    
    return {
        'data': heatmap,
        'max_value': max_value,
        'weekdays': ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'],
        'hours': [f'{h:02d}:00' for h in range(24)]
    }


# ========== ТАБЛИЦЫ ==========

def get_time_analysis(queryset):
    """Анализ по времени: часы и дни недели"""
    
    hours_data = {}
    for hour in range(24):
        hours_data[hour] = {'count': 0, 'models': {}}
    
    weekdays_data = {}
    for day in range(7):
        weekdays_data[day] = {'count': 0, 'hours': {}}
    
    total = queryset.count()
    
    for lead in queryset:
        # Конвертируем UTC в локальное время
        local_time = lead.created_at.astimezone(django_tz.get_current_timezone())
        hour = local_time.hour 
        weekday = local_time.weekday()
        
        hours_data[hour]['count'] += 1
        if lead.product:
            hours_data[hour]['models'][lead.product] = hours_data[hour]['models'].get(lead.product, 0) + 1
        
        weekdays_data[weekday]['count'] += 1
        weekdays_data[weekday]['hours'][hour] = weekdays_data[weekday]['hours'].get(hour, 0) + 1
    
    # По часам
    hours_list = []
    for hour in range(24):
        data = hours_data[hour]
        top_model = max(data['models'].items(), key=lambda x: x[1])[0] if data['models'] else '—'
        
        hours_list.append({
            'hour': f'{hour:02d}:00',
            'count': data['count'],
            'percent': round(data['count'] / total * 100, 1) if total > 0 else 0,
            'top_model': top_model,
            'avg_time': 11  # Заглушка
        })
    
    # По дням недели
    weekday_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    weekdays_list = []
    
    for day in range(7):
        data = weekdays_data[day]
        top_hour = max(data['hours'].items(), key=lambda x: x[1])[0] if data['hours'] else 12
        
        weekdays_list.append({
            'day': weekday_names[day],
            'count': data['count'],
            'percent': round(data['count'] / total * 100, 1) if total > 0 else 0,
            'top_hour': f'{top_hour:02d}:00',
            'avg_time': 11
        })
    
    return {
        'by_hours': hours_list,
        'by_weekdays': weekdays_list
    }


def get_utm_campaigns(queryset):
    """UTM кампании"""
    campaigns = {}
    
    for lead in queryset:
        if not lead.utm_data or lead.utm_data == '':
            continue
        
        try:
            utm = json.loads(lead.utm_data)
            source = utm.get('utm_source', 'unknown')
            medium = utm.get('utm_medium', 'unknown')
            campaign = utm.get('utm_campaign', 'unknown')
            
            key = f"{source}|{medium}|{campaign}"
            
            if key not in campaigns:
                campaigns[key] = {
                    'source': source,
                    'medium': medium,
                    'campaign': campaign,
                    'count': 0
                }
            
            campaigns[key]['count'] += 1
        except:
            pass
    
    campaigns_list = sorted(campaigns.values(), key=lambda x: x['count'], reverse=True)
    return campaigns_list[:20]

def _get_referer_data(queryset):
    """
    Распределение по источникам перехода (Referer)
    """
    referers = {}
    total = queryset.count()
    
    for lead in queryset:
        # Определяем источник через нашу функцию
        source_key = _get_source_from_utm(lead)
        
        # Группируем по источнику
        if source_key == 'direct':
            referer_name = 'Прямой заход'
        elif source_key == 'google':
            referer_name = 'Google'
        elif source_key == 'facebook':
            referer_name = 'Facebook'
        elif source_key == 'instagram':
            referer_name = 'Instagram'
        elif source_key == 'yandex':
            referer_name = 'Яндекс'
        elif source_key == 'telegram':
            referer_name = 'Telegram'
        elif source_key == 'tiktok':
            referer_name = 'TikTok'
        elif source_key == 'youtube':
            referer_name = 'YouTube'
        else:
            # Если "other" — показываем реальный referer
            if lead.referer and lead.referer != '':
                referer_name = lead.referer[:50]  # Обрезаем длинные URL
            else:
                referer_name = 'Другие'
        
        referers[referer_name] = referers.get(referer_name, 0) + 1
    
    # Сортируем по убыванию
    sorted_referers = sorted(referers.items(), key=lambda x: x[1], reverse=True)
    
    result = []
    for referer, count in sorted_referers[:10]:  # Топ-10
        percent = round(count / total * 100, 1) if total > 0 else 0
        result.append({
            'referer': referer,
            'count': count,
            'percent': percent
        })
    
    return result

def get_region_model_matrix(queryset):
    """Матрица Регион × Модель"""
    from main.models import REGION_CHOICES
    
    matrix = {}
    
    for lead in queryset:
        region = lead.get_region_display().replace(' viloyati', '').replace(' shahri', '')
        product = lead.product or 'Не указано'
        
        if region not in matrix:
            matrix[region] = {}
        
        matrix[region][product] = matrix[region].get(product, 0) + 1
    
    # Топ-5 моделей
    all_products = {}
    for lead in queryset:
        product = lead.product or 'Не указано'
        all_products[product] = all_products.get(product, 0) + 1
    
    top_products = sorted(all_products.items(), key=lambda x: x[1], reverse=True)[:5]
    top_products_names = [p[0] for p in top_products]
    
    result = {
        'regions': list(matrix.keys()),
        'models': top_products_names,
        'data': []
    }
    
    for region in matrix.keys():
        row = []
        for product in top_products_names:
            row.append(matrix[region].get(product, 0))
        result['data'].append(row)
    
    return result


def get_source_model_matrix(queryset):
    """Матрица Источник × Модель"""
    matrix = {
        'Google': {},
        'Яндекс': {},
        'Instagram': {},
        'Facebook': {},
        'Telegram': {},
        'TikTok': {},
        'YouTube': {},
        'Прямые': {},
        'Другие': {}
    }
    
    source_map = {
        'google': 'Google',
        'yandex': 'Яндекс',
        'instagram': 'Instagram',
        'facebook': 'Facebook',
        'telegram': 'Telegram',
        'tiktok': 'TikTok',
        'youtube': 'YouTube',
        'direct': 'Прямые',
        'other': 'Другие'
    }
    

    for lead in queryset:
        product = lead.product or 'Не указано'
        source_key = _get_source_from_utm(lead)
        source_name = source_map[source_key]
        
        matrix[source_name][product] = matrix[source_name].get(product, 0) + 1
    
    # Топ-5 моделей
    all_products = {}
    for lead in queryset:
        product = lead.product or 'Не указано'
        all_products[product] = all_products.get(product, 0) + 1
    
    top_products = sorted(all_products.items(), key=lambda x: x[1], reverse=True)[:5]
    top_products_names = [p[0] for p in top_products]
    
    result = {
        'sources': list(matrix.keys()),
        'models': top_products_names,
        'data': []
    }
    
    for source in matrix.keys():
        row = []
        for product in top_products_names:
            row.append(matrix[source].get(product, 0))
        result['data'].append(row)
    
    return result


def get_behavior_data(queryset):
    """Поведение клиентов (повторные обращения)"""
    
    phones = {}
    for lead in queryset:
        phone = lead.phone
        if phone not in phones:
            phones[phone] = []
        phones[phone].append(lead)
    
    total_leads = queryset.count()
    unique_clients = len(phones)
    repeat_clients = sum(1 for leads in phones.values() if len(leads) > 1)
    
    repeat_clients_list = []
    
    for phone, leads in phones.items():
        if len(leads) < 2:
            continue
        
        leads_sorted = sorted(leads, key=lambda x: x.created_at)
        models = [lead.product or 'Не указано' for lead in leads_sorted]
        
        first_date = leads_sorted[0].created_at
        last_date = leads_sorted[-1].created_at
        interval_days = (last_date - first_date).days
        
        repeat_clients_list.append({
            'name': leads_sorted[0].name,
            'phone': phone,
            'count': len(leads),
            'models': ', '.join(models[:3]) + ('...' if len(models) > 3 else ''),
            'interval_days': interval_days,
            'last_date': last_date.strftime('%d.%m.%Y')
        })
    
    repeat_clients_list.sort(key=lambda x: x['count'], reverse=True)
    
    return {
        'total_leads': total_leads,
        'unique_clients': unique_clients,
        'repeat_clients': repeat_clients,
        'repeat_percent': round(repeat_clients / unique_clients * 100, 1) if unique_clients > 0 else 0,
        'clients_list': repeat_clients_list[:100]
    }