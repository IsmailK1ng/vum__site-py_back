import requests
import logging
import json
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
import pytz

logger = logging.getLogger('django')


class TelegramReportSender:
    """Отправка отчётов в Telegram"""
    
    @classmethod
    def send_daily_report(cls):
        """Ежедневный отчёт в 20:00"""
        try:
            from main.models import ContactForm
            
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID
            
            if not bot_token or not chat_id:
                logger.warning("Telegram настройки не заданы")
                return
            
            # Временная зона
            tz = pytz.timezone(settings.TIME_ZONE)
            now = timezone.now().astimezone(tz)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = now
            
            # День недели
            weekday_names = {
                0: 'понедельник',
                1: 'вторник',
                2: 'среда',
                3: 'четверг',
                4: 'пятница',
                5: 'суббота',
                6: 'воскресенье'
            }
            weekday = weekday_names[now.weekday()]
            
            # Заявки за сегодня
            today_leads = ContactForm.objects.filter(
                created_at__gte=today_start,
                created_at__lte=today_end
            )
            
            total_today = today_leads.count()
            
            # Прошлый такой же день недели
            last_same_day = today_start - timedelta(days=7)
            last_same_day_end = last_same_day + timedelta(days=1)
            last_week_count = ContactForm.objects.filter(
                created_at__gte=last_same_day,
                created_at__lt=last_same_day_end
            ).count()
            
            # Разница
            diff = total_today - last_week_count
            diff_percent = round((diff / last_week_count * 100), 1) if last_week_count > 0 else 0
            diff_arrow = "↗️" if diff >= 0 else "↘️"
            
            # Средняя за неделю
            week_start = today_start - timedelta(days=7)
            week_avg = round(ContactForm.objects.filter(
                created_at__gte=week_start,
                created_at__lt=today_start
            ).count() / 7, 1)
            
            avg_diff = total_today - week_avg
            avg_diff_percent = round((avg_diff / week_avg * 100), 1) if week_avg > 0 else 0
            avg_arrow = "↗️" if avg_diff >= 0 else "↘️"
            
            # amoCRM статистика
            amocrm_sent = today_leads.filter(amocrm_status='sent').count()
            amocrm_failed = today_leads.filter(amocrm_status='failed').count()
            amocrm_conversion = round((amocrm_sent / total_today * 100), 0) if total_today > 0 else 0
            
            # Популярные модели
            models_stat = today_leads.exclude(product__isnull=True).exclude(product='').values('product').annotate(
                count=Count('id')
            ).order_by('-count')[:4]
            
            # Регионы
            regions_stat = today_leads.values('region').annotate(
                count=Count('id')
            ).order_by('-count')[:4]
            
            # Пиковые часы
            hours_stat = {}
            for lead in today_leads:
                hour = lead.created_at.astimezone(tz).hour
                hour_range = f"{hour:02d}:00-{hour+1:02d}:00"
                hours_stat[hour_range] = hours_stat.get(hour_range, 0) + 1
            
            top_hours = sorted(hours_stat.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # UTM источники
            utm_stat = {}
            for lead in today_leads:
                if lead.utm_data:
                    try:
                        utm = json.loads(lead.utm_data)
                        source = utm.get('utm_source', 'Неизвестно')
                        utm_stat[source] = utm_stat.get(source, 0) + 1
                    except:
                        pass
            
            # Прямые заходы
            direct_count = today_leads.filter(Q(utm_data__isnull=True) | Q(utm_data='')).count()
            if direct_count > 0:
                utm_stat['Прямые'] = direct_count
            
            top_sources = sorted(utm_stat.items(), key=lambda x: x[1], reverse=True)[:4]
            
            # Формируем сообщение
            message = f"🌆 ОТЧЁТ ЗА СЕГОДНЯ ({now.strftime('%d.%m.%Y')}, {weekday})\n"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            message += f"\n📥 Получено заявок: {total_today}"
            message += f"\n  {diff_arrow} {'+' if diff >= 0 else ''}{diff} к прошлому {weekday}у ({last_same_day.strftime('%d.%m')})"
            message += f"\n  {avg_arrow} {'+' if avg_diff >= 0 else ''}{avg_diff_percent:+.0f}% к среднему за неделю"
            
            message += f"\n\n🎯 Конверсия amoCRM: {amocrm_conversion:.0f}%"
            if amocrm_failed > 0:
                message += f" ({amocrm_failed} ошибка)" if amocrm_failed == 1 else f" ({amocrm_failed} ошибки)"
            
            message += "\n\n━━━━━━━━━━━━━━━━━━━━\n"
            
            # Модели
            if models_stat:
                message += "\n🚗 Популярные модели сегодня:"
                for i, item in enumerate(models_stat, 1):
                    percent = round((item['count'] / total_today * 100), 0)
                    message += f"\n  {i}️⃣ {item['product']} — {item['count']} заявок ({percent:.0f}%)"
                
                others = total_today - sum(item['count'] for item in models_stat)
                if others > 0:
                    percent = round((others / total_today * 100), 0)
                    message += f"\n  {len(models_stat)+1}️⃣ Остальные — {others} заявок ({percent:.0f}%)"
            
            # Регионы
            if regions_stat:
                message += "\n\n📍 По регионам:"
                region_emoji = {
                    'Toshkent shahri': '🏙️',
                    'Samarqand viloyati': '🕌',
                    'Buxoro viloyati': '🏛️',
                }
                
                for i, item in enumerate(regions_stat, 1):
                    emoji = region_emoji.get(item['region'], '🌄')
                    percent = round((item['count'] / total_today * 100), 0)
                    message += f"\n  {emoji} {item['region']} — {item['count']} ({percent:.0f}%)"
                
                others = total_today - sum(item['count'] for item in regions_stat)
                if others > 0:
                    percent = round((others / total_today * 100), 0)
                    message += f"\n  🌄 Остальные — {others} ({percent:.0f}%)"
            
            # Пиковые часы
            if top_hours:
                message += "\n\n⏰ Пиковые часы:"
                for i, (hour_range, count) in enumerate(top_hours, 1):
                    emoji = "🔥" if i == 1 else ""
                    message += f"\n  {hour_range} — {count} заявок {emoji}"
            
            # Источники
            if top_sources:
                message += "\n\n🔗 Источники:"
                source_emoji = {
                    'google': '📊 Google Ads',
                    'instagram': '📱 Instagram',
                    'facebook': '📘 Facebook',
                    'Прямые': '👥 Прямые'
                }
                
                for i, (source, count) in enumerate(top_sources, 1):
                    source_name = source_emoji.get(source, f"🔗 {source.title()}")
                    percent = round((count / total_today * 100), 0)
                    message += f"\n  {source_name} — {count} ({percent:.0f}%)"
            
            # Отправляем
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Ежедневный отчёт Telegram отправлен")
            else:
                logger.error(f"Ошибка отправки отчёта: {response.text[:200]}")
        
        except Exception as e:
            logger.error(f"Ошибка формирования отчёта: {str(e)}", exc_info=True)
    
    @classmethod
    def send_weekly_report(cls):
        """Еженедельный отчёт в понедельник 10:00"""
        try:
            from main.models import ContactForm
            
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID
            
            if not bot_token or not chat_id:
                logger.warning("Telegram настройки не заданы")
                return
            
            # Временная зона
            tz = pytz.timezone(settings.TIME_ZONE)
            now = timezone.now().astimezone(tz)
            
            # Прошлая неделя (ПН-ВС)
            # Сегодня понедельник, значит прошлая неделя = 7 дней назад до вчера
            last_monday = now - timedelta(days=now.weekday() + 7)
            last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            last_sunday = last_monday + timedelta(days=7)
            
            # Заявки за прошлую неделю
            week_leads = ContactForm.objects.filter(
                created_at__gte=last_monday,
                created_at__lt=last_sunday
            )
            
            total_week = week_leads.count()
            
            # Позапрошлая неделя (для сравнения)
            prev_week_start = last_monday - timedelta(days=7)
            prev_week_end = last_monday
            prev_week_count = ContactForm.objects.filter(
                created_at__gte=prev_week_start,
                created_at__lt=prev_week_end
            ).count()
            
            # Разница
            diff = total_week - prev_week_count
            diff_percent = round((diff / prev_week_count * 100), 1) if prev_week_count > 0 else 0
            diff_arrow = "↗️" if diff >= 0 else "↘️"
            
            # Средняя скорость обработки (примерно, можно улучшить)
            avg_speed = 11  # минут (заглушка, можно добавить реальный расчёт)
            
            # amoCRM статистика
            amocrm_sent = week_leads.filter(amocrm_status='sent').count()
            amocrm_failed = week_leads.filter(amocrm_status='failed').count()
            amocrm_conversion = round((amocrm_sent / total_week * 100), 0) if total_week > 0 else 0
            
            # По дням недели
            days_stat = {}
            weekday_names = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
            weekday_full_names = {
                0: 'Понедельник',
                1: 'Вторник',
                2: 'Среда',
                3: 'Четверг',
                4: 'Пятница',
                5: 'Суббота',
                6: 'Воскресенье'
            }
            
            for i in range(7):
                day_start = last_monday + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                count = ContactForm.objects.filter(
                    created_at__gte=day_start,
                    created_at__lt=day_end
                ).count()
                days_stat[i] = {
                    'name': weekday_full_names[i],
                    'short': weekday_names[i],
                    'date': day_start.strftime('%d.%m'),
                    'count': count,
                    'percent': round((count / total_week * 100), 0) if total_week > 0 else 0
                }
            
            # Пиковый день
            peak_day = max(days_stat.items(), key=lambda x: x[1]['count'])
            
            # Пиковые часы
            hours_stat = {}
            for lead in week_leads:
                hour = lead.created_at.astimezone(tz).hour
                hour_range = f"{hour:02d}:00-{hour+1:02d}:00"
                hours_stat[hour_range] = hours_stat.get(hour_range, 0) + 1
            
            top_hours = sorted(hours_stat.items(), key=lambda x: x[1], reverse=True)[:4]
            
            # Популярные модели
            models_stat = week_leads.exclude(product__isnull=True).exclude(product='').values('product').annotate(
                count=Count('id')
            ).order_by('-count')[:6]
            
            # Регионы
            regions_stat = week_leads.values('region').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # UTM источники
            utm_sources = {}
            for lead in week_leads:
                if lead.utm_data:
                    try:
                        utm = json.loads(lead.utm_data)
                        source = utm.get('utm_source', 'Неизвестно')
                        utm_sources[source] = utm_sources.get(source, 0) + 1
                    except:
                        pass
            
            direct_count = week_leads.filter(Q(utm_data__isnull=True) | Q(utm_data='')).count()
            if direct_count > 0:
                utm_sources['Прямые заходы'] = direct_count
            
            top_sources = sorted(utm_sources.items(), key=lambda x: x[1], reverse=True)
            
            # UTM кампании
            utm_campaigns = {}
            for lead in week_leads:
                if lead.utm_data:
                    try:
                        utm = json.loads(lead.utm_data)
                        source = utm.get('utm_source', 'unknown')
                        medium = utm.get('utm_medium', 'unknown')
                        campaign = utm.get('utm_campaign', 'unknown')
                        key = f"{source} / {medium} / {campaign}"
                        utm_campaigns[key] = utm_campaigns.get(key, 0) + 1
                    except:
                        pass
            
            top_campaigns = sorted(utm_campaigns.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Конверсия по каналам
            channel_conversion = {}
            for source, count in top_sources[:3]:
                channel_leads = []
                for lead in week_leads:
                    if lead.utm_data:
                        try:
                            utm = json.loads(lead.utm_data)
                            if utm.get('utm_source') == source:
                                channel_leads.append(lead)
                        except:
                            pass
                    elif source == 'Прямые заходы' and (not lead.utm_data or lead.utm_data == ''):
                        channel_leads.append(lead)
                
                if channel_leads:
                    # Топ продукты для этого канала
                    products = {}
                    for lead in channel_leads:
                        if lead.product:
                            products[lead.product] = products.get(lead.product, 0) + 1
                    
                    top_products = sorted(products.items(), key=lambda x: x[1], reverse=True)[:3]
                    channel_conversion[source] = {
                        'count': len(channel_leads),
                        'products': top_products
                    }
            
            # Формируем сообщение
            message = f"📊 ПОЛНЫЙ ОТЧЁТ ЗА НЕДЕЛЮ ({last_monday.strftime('%d.%m')} - {(last_sunday - timedelta(days=1)).strftime('%d.%m')})\n"
            
            message += "\n━━━━━━━━━━━━━━━━━━━━"
            message += "\n📈 ОБЩАЯ СТАТИСТИКА"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            message += f"\n📥 Всего заявок: {total_week}"
            message += f"\n  {diff_arrow} {'+' if diff >= 0 else ''}{diff} к прошлой неделе ({diff_percent:+.1f}%)"
            
            message += f"\n\n⏱️ Средняя скорость обработки: {avg_speed} минут"
            
            message += f"\n\n🎯 Конверсия amoCRM: {amocrm_conversion:.0f}%"
            if amocrm_failed > 0:
                message += f" ({amocrm_failed} ошибок)" if amocrm_failed > 1 else f" ({amocrm_failed} ошибка)"
            
            message += "\n\n━━━━━━━━━━━━━━━━━━━━"
            message += "\n📅 АНАЛИТИКА ПО ДНЯМ"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            for i in range(7):
                day = days_stat[i]
                emoji = "🔥" if i == peak_day[0] else ""
                message += f"\n{day['short']} {day['date']} — {day['count']} заявок ({day['percent']:.0f}%) {emoji}"
            
            message += f"\n\n💡 Вывод: {peak_day[1]['name']} — самый продуктивный день"
            
            message += "\n\n━━━━━━━━━━━━━━━━━━━━"
            message += "\n⏰ ПИКОВЫЕ ЧАСЫ"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, (hour_range, count) in enumerate(top_hours, 1):
                emoji = "🔥" if i == 1 else ""
                message += f"\n{hour_range} — {count} заявок {emoji}"
            
            top_hour_range = top_hours[0][0] if top_hours else "14:00-15:00"
            message += f"\n\n💡 Вывод: Обеденное время ({top_hour_range}) — пик активности"
            
            message += "\n\n━━━━━━━━━━━━━━━━━━━━"
            message += "\n🚗 ПОПУЛЯРНЫЕ МОДЕЛИ"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, item in enumerate(models_stat, 1):
                percent = round((item['count'] / total_week * 100), 0)
                message += f"\n{i}️⃣ {item['product']} — {item['count']} заявок ({percent:.0f}%)"
            
            others = total_week - sum(item['count'] for item in models_stat)
            if others > 0:
                percent = round((others / total_week * 100), 0)
                message += f"\n{len(models_stat)+1}️⃣ Остальные — {others} заявок ({percent:.0f}%)"
            
            if models_stat:
                top_model = models_stat[0]['product']
                message += f"\n\n💡 Вывод: {top_model} лидирует с большим отрывом"
            
            message += "\n\n━━━━━━━━━━━━━━━━━━━━"
            message += "\n📍 ГЕОГРАФИЯ ЗАЯВОК"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            region_emoji = {
                'Toshkent shahri': '🏙️',
                'Samarqand viloyati': '🕌',
                'Buxoro viloyati': '🏛️',
                'Fargʻona viloyati': '🌄',
                'Namangan viloyati': '🏔️',
            }
            
            for i, item in enumerate(regions_stat[:6], 1):
                emoji = region_emoji.get(item['region'], '⭐')
                percent = round((item['count'] / total_week * 100), 0)
                region_name = item['region'].replace(' viloyati', '').replace(' shahri', '')
                message += f"\n{emoji} {region_name} — {item['count']} ({percent:.0f}%)"
            
            if regions_stat:
                top_region = regions_stat[0]['region'].replace(' viloyati', '').replace(' shahri', '')
                top_region_percent = round((regions_stat[0]['count'] / total_week * 100), 0)
                message += f"\n\n💡 Вывод: {top_region} даёт {top_region_percent}% всех заявок"
            
            message += "\n\n━━━━━━━━━━━━━━━━━━━━"
            message += "\n🔗 ИСТОЧНИКИ ТРАФИКА"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            source_emoji = {
                'google': '📊 Google Ads',
                'instagram': '📱 Instagram',
                'facebook': '📘 Facebook',
                'Прямые заходы': '👥 Прямые заходы'
            }
            
            for i, (source, count) in enumerate(top_sources, 1):
                source_name = source_emoji.get(source, f"🔗 {source.title()}")
                percent = round((count / total_week * 100), 0)
                message += f"\n{source_name} — {count} заявок ({percent:.0f}%)"
            
            message += "\n\n━━━━━━━━━━━━━━━━━━━━"
            message += "\n💰 ЛУЧШИЕ UTM КАМПАНИИ"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, (campaign, count) in enumerate(top_campaigns, 1):
                message += f"\n{i}️⃣ {campaign} — {count} заявок"
            
            message += "\n\n━━━━━━━━━━━━━━━━━━━━"
            message += "\n📊 КОНВЕРСИЯ ПО КАНАЛАМ"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            for source, data in list(channel_conversion.items())[:3]:
                source_name = source_emoji.get(source, source.title())
                message += f"\n{source_name}:"
                
                for product, count in data['products']:
                    percent = round((count / data['count'] * 100), 0)
                    message += f"\n  • {product} → {count} заявок ({percent:.0f}%)"
            
            message += "\n\n━━━━━━━━━━━━━━━━━━━━"
            message += "\n💡 РЕКОМЕНДАЦИИ ДЛЯ МАРКЕТОЛОГОВ"
            message += "\n━━━━━━━━━━━━━━━━━━━━\n"
            
            message += "\n✅ ЧТО РАБОТАЕТ ХОРОШО:"
            
            # Рекомендации на основе данных
            if peak_day[1]['count'] > 0:
                message += f"\n  • {peak_day[1]['name']} — усилить рекламу в этот день"
            
            if top_hours:
                message += f"\n  • {top_hours[0][0]} — пик активности, увеличить ставки"
            
            if top_sources:
                top_source_name = source_emoji.get(top_sources[0][0], top_sources[0][0].title())
                top_source_percent = round((top_sources[0][1] / total_week * 100), 0)
                message += f"\n  • {top_source_name} даёт стабильно {top_source_percent}%+ заявок"
            
            if top_campaigns:
                campaign_name = top_campaigns[0][0].split(' / ')[-1]  # только название кампании
                message += f"\n  • Кампания \"{campaign_name}\" работает лучше всего"
            
            if regions_stat:
                top_region_name = regions_stat[0]['region'].replace(' viloyati', '').replace(' shahri', '')
                message += f"\n  • {top_region_name} — основной рынок"
            
            message += "\n\n⚠️ НА ЧТО ОБРАТИТЬ ВНИМАНИЕ:"
            
            # Находим слабые дни
            min_day = min(days_stat.items(), key=lambda x: x[1]['count'])
            if min_day[1]['count'] < total_week / 7 * 0.5:  # меньше 50% от среднего
                message += f"\n  • {min_day[1]['name']} — мало заявок ({min_day[1]['percent']}%), снизить бюджет"
            
            # Регионы с потенциалом
            if len(regions_stat) > 1:
                second_region = regions_stat[1]['region'].replace(' viloyati', '').replace(' shahri', '')
                second_percent = round((regions_stat[1]['count'] / total_week * 100), 0)
                if second_percent < 30:
                    message += f"\n  • Регионы кроме {top_region_name} — потенциал роста +30%"
            
            # Если Instagram < 20%
            instagram_count = utm_sources.get('instagram', 0)
            if instagram_count > 0:
                instagram_percent = round((instagram_count / total_week * 100), 0)
                if instagram_percent < 20:
                    message += f"\n  • Instagram можно усилить (только {instagram_percent}%)"
            
            message += "\n\n🎯 ДЕЙСТВИЯ НА СЛЕДУЮЩУЮ НЕДЕЛЮ:"
            
            # Топ источник
            if top_sources:
                top_source_name = source_emoji.get(top_sources[0][0], top_sources[0][0].title())
                message += f"\n  • Увеличить бюджет {top_source_name} на 20%"
            
            # Топ модель
            if models_stat:
                message += f"\n  • Запустить новую кампанию {models_stat[0]['product']} на {peak_day[1]['name'].lower()}"
            
            # Регионы
            if len(regions_stat) > 1:
                second_region = regions_stat[1]['region'].replace(' viloyati', '').replace(' shahri', '')
                message += f"\n  • Усилить таргетинг на {second_region}"
            
            # Отправляем
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Еженедельный отчёт Telegram отправлен")
            else:
                logger.error(f"Ошибка отправки недельного отчёта: {response.text[:200]}")
        
        except Exception as e:
            logger.error(f"Ошибка формирования недельного отчёта: {str(e)}", exc_info=True)
