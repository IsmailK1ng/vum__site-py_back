import json
import logging

import pytz
import requests
from django.conf import settings

logger = logging.getLogger('bot')  


class TelegramNotificationSender:

    @classmethod
    def send_lead_notification(cls, contact_form) -> None:
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id   = settings.TELEGRAM_CHAT_ID

            if not bot_token or not chat_id:
                logger.warning('Telegram settings not configured in .env')
                return

            message      = cls._format_message(contact_form)
            reply_markup = cls._build_keyboard(contact_form)

            payload = {
                'chat_id':                  chat_id,
                'text':                     message,
                'parse_mode':               'HTML',
                'disable_web_page_preview': True,
            }
            if reply_markup:
                payload['reply_markup'] = reply_markup

            response = requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                json=payload,
                timeout=5,
            )

            if response.status_code == 200:
                logger.info('Telegram notification sent lead#%s', contact_form.id)
            else:
                logger.error(
                    'Telegram error status=%s lead#%s: %s',
                    response.status_code,
                    contact_form.id,
                    response.text[:200],
                )

        except requests.exceptions.Timeout:
            logger.error('Telegram timeout lead#%s', contact_form.id)

        except requests.exceptions.RequestException as exc:
            logger.error('Telegram request error lead#%s: %s', contact_form.id, exc)

        except Exception as exc:
            logger.error(
                'Telegram unexpected error lead#%s: %s',
                contact_form.id, exc, exc_info=True,
            )

    @staticmethod
    def _format_message(contact_form) -> str:
        if contact_form.amocrm_status == 'failed':
            header = f'Новая заявка FAW.UZ #{contact_form.id}\nНе отправлено в amoCRM\n'
        else:
            header = f'Новая заявка FAW.UZ #{contact_form.id}\n'

        message  = header
        message += f'\nКлиент: {contact_form.name}'
        message += f'\nТелефон: {contact_form.phone}'
        message += f'\nРегион: {contact_form.get_region_display()}'

        if contact_form.product:
            message += f'\nМодель: {contact_form.product}'

        if contact_form.message:
            msg = contact_form.message.strip()
            if len(msg) > 500:
                msg = msg[:497] + '...'
            message += f'\n\nСообщение:\n{msg}'

        message += '\n\nИсточник:'

        if contact_form.referer:
            referer = (
                contact_form.referer
                .replace('https://', '')
                .replace('http://', '')
                .replace('www.', '')
            )
            if '?' in referer:
                referer = referer.split('?')[0]
            if len(referer) > 80:
                referer = referer[:77] + '...'
            message += f'\nReferer: {referer}'

        if contact_form.utm_data:
            try:
                utm = json.loads(contact_form.utm_data)
                parts = [
                    utm[k] for k in ('utm_source', 'utm_medium', 'utm_campaign')
                    if utm.get(k)
                ]
                if parts:
                    message += f"\nUTM: {' / '.join(parts)}"
            except Exception:
                pass

        message += '\nForm ID: Заявка с сайта FAW.UZ'

        if contact_form.visitor_uid:
            uid = contact_form.visitor_uid
            if len(uid) > 20:
                uid = uid[:20] + '...'
            message += f'\nVisitor UID: {uid}'

        if contact_form.amocrm_status == 'failed' and contact_form.amocrm_error:
            error = contact_form.amocrm_error.strip()
            if len(error) > 200:
                error = error[:197] + '...'
            message += f'\n\nОшибка amoCRM: {error}'

        tz = pytz.timezone(settings.TIME_ZONE)
        created_local = contact_form.created_at.astimezone(tz)
        message += f'\n\n{created_local.strftime("%d.%m.%Y в %H:%M")}'

        return message

    @staticmethod
    def _build_keyboard(contact_form) -> dict | None:
        buttons = []

        if contact_form.amocrm_status == 'sent' and contact_form.amocrm_lead_id:
            buttons.append({
                'text': 'Открыть в amoCRM',
                'url':  f'https://fawtrucks.amocrm.ru/leads/detail/{contact_form.amocrm_lead_id}',
            })

        buttons.append({
            'text': 'Админ-панель FAW',
            'url':  f'https://faw.uz/admin/main/contactform/{contact_form.id}/change/',
        })

        return {'inline_keyboard': [buttons]} if buttons else None