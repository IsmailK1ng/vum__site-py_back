import json
import logging

import requests
from django.conf import settings
from django.utils import timezone

from main.models import AmoCRMToken
from main.services.amocrm.token_manager import TokenManager

logger = logging.getLogger('amocrm')


class LeadSender:

    @classmethod
    def send_lead(cls, contact_form) -> None:
        if contact_form.amocrm_status == 'sent' and contact_form.amocrm_lead_id:
            return

        try:
            token_obj = AmoCRMToken.get_instance()

            if token_obj.is_expired():
                TokenManager.refresh_token(token_obj)
                token_obj.refresh_from_db()

            pipeline_id = settings.AMOCRM_PIPELINE_ID
            editable_status = cls._get_editable_status_for_pipeline(
                token_obj.access_token, pipeline_id,
            )
            status_to_use = editable_status or settings.AMOCRM_STATUS_ID

            extra_tags, lead_name_override = cls._resolve_lead_meta(contact_form)
            lead_data = cls._prepare_lead_data(
                contact_form, pipeline_id, status_to_use,
                extra_tags=extra_tags,
                lead_name_override=lead_name_override,
            )

            headers = {
                'Authorization': f'Bearer {token_obj.access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.post(
                f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/complex',
                json=lead_data,
                headers=headers,
                timeout=10,
            )

            if response.status_code in (200, 201):
                result = response.json()
                lead_id = cls._extract_lead_id(result)

                if lead_id:
                    contact_form.amocrm_status  = 'sent'
                    contact_form.amocrm_lead_id = lead_id
                    contact_form.amocrm_sent_at = timezone.now()
                    contact_form.amocrm_error   = None
                    contact_form.save(update_fields=[
                        'amocrm_status',
                        'amocrm_lead_id',
                        'amocrm_sent_at',
                        'amocrm_error',
                    ])
                    cls._patch_utm_fields(lead_id, contact_form, headers)
                else:
                    raise ValueError('Lead ID not found in amoCRM response')
            else:
                error_text = cls._parse_error_response(response)
                logger.error(
                    'AmoCRM error status=%s: %s', response.status_code, error_text,
                )
                contact_form.amocrm_status = 'failed'
                contact_form.amocrm_error  = error_text[:500]
                contact_form.save(update_fields=['amocrm_status', 'amocrm_error'])

        except requests.exceptions.Timeout:
            logger.error('AmoCRM connection timeout lead#%s', contact_form.id)
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error  = 'Connection timeout'
            contact_form.save(update_fields=['amocrm_status', 'amocrm_error'])

        except requests.exceptions.RequestException as exc:
            logger.error('AmoCRM request error lead#%s: %s', contact_form.id, exc)
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error  = str(exc)[:500]
            contact_form.save(update_fields=['amocrm_status', 'amocrm_error'])

        except Exception as exc:
            logger.error(
                'AmoCRM unexpected error lead#%s: %s',
                contact_form.id, exc, exc_info=True,
            )
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error  = f'{type(exc).__name__}: {exc}'[:500]
            contact_form.save(update_fields=['amocrm_status', 'amocrm_error'])

    @classmethod
    def _patch_utm_fields(cls, lead_id, contact_form, headers) -> None:
        if not contact_form.utm_data:
            return

        try:
            utm = json.loads(contact_form.utm_data)
        except (json.JSONDecodeError, TypeError):
            return

        if not isinstance(utm, dict):
            return

        utm_field_map = {
            'utm_source':   settings.AMOCRM_FIELD_UTM_SOURCE,
            'utm_medium':   settings.AMOCRM_FIELD_UTM_MEDIUM,
            'utm_campaign': settings.AMOCRM_FIELD_UTM_CAMPAIGN,
            'utm_term':     settings.AMOCRM_FIELD_UTM_TERM,
            'utm_content':  settings.AMOCRM_FIELD_UTM_CONTENT,
            'utm_referrer': settings.AMOCRM_FIELD_UTM_REFERRER,
        }

        custom_fields = [
            {'field_id': field_id, 'values': [{'value': utm.get(key, '').strip()[:500]}]}
            for key, field_id in utm_field_map.items()
            if utm.get(key, '').strip()
        ]

        if not custom_fields:
            return

        try:
            response = requests.patch(
                f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/{lead_id}',
                headers=headers,
                json={'custom_fields_values': custom_fields},
                timeout=10,
            )
            if response.status_code == 200:
                logger.info('AmoCRM UTM fields updated lead_id=%s', lead_id)
            else:
                logger.error(
                    'AmoCRM UTM patch failed lead_id=%s status=%s',
                    lead_id, response.status_code,
                )
        except Exception as exc:
            logger.error('AmoCRM UTM patch exception lead_id=%s: %s', lead_id, exc)

    @staticmethod
    def _get_editable_status_for_pipeline(access_token: str, pipeline_id) -> int | None:
        try:
            url = (
                f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru'
                f'/api/v4/leads/pipelines/{pipeline_id}/statuses'
            )
            resp = requests.get(
                url,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            resp.raise_for_status()
            statuses = resp.json().get('_embedded', {}).get('statuses', [])
            for s in statuses:
                if s.get('is_editable', False):
                    return s.get('id')
            return None
        except Exception as exc:
            logger.warning(
                'Could not fetch pipeline statuses pipeline_id=%s: %s',
                pipeline_id, exc,
            )
            return None

    @staticmethod
    def _extract_lead_id(result) -> int | None:
        try:
            if isinstance(result, list) and result:
                first = result[0]
                if 'id' in first:
                    return first['id']
                leads = first.get('_embedded', {}).get('leads', [])
                if leads:
                    return leads[0]['id']
            return None
        except (KeyError, IndexError, TypeError) as exc:
            logger.error('AmoCRM lead ID parse error: %s', exc)
            return None

    @staticmethod
    def _parse_error_response(response) -> str:
        try:
            error_data = response.json()
            if 'validation-errors' in error_data:
                errors = error_data['validation-errors']
                if errors and 'errors' in errors[0]:
                    first = errors[0]['errors'][0]
                    return f"{first.get('code')}: {first.get('detail')}"
            return error_data.get('detail') or error_data.get('title') or response.text[:200]
        except Exception:
            return response.text[:200]

    @staticmethod
    def _prepare_lead_data(
        contact_form,
        pipeline_id,
        status_id,
        extra_tags: list[str] | None = None,
        lead_name_override: str | None = None,
    ) -> list[dict]:
        name_parts = contact_form.name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name  = name_parts[1] if len(name_parts) > 1 else ''

        lead_custom_fields = [
            {
                'field_id': settings.AMOCRM_FIELD_REGION,
                'values':   [{'value': contact_form.get_region_display()}],
            }
        ]

        if contact_form.message:
            msg = contact_form.message.strip()
            if len(msg) > 1000:
                msg = msg[:997] + '...'
            lead_custom_fields.append({
                'field_id': settings.AMOCRM_FIELD_MESSAGE,
                'values':   [{'value': msg}],
            })

        if contact_form.product:
            lead_custom_fields.append({
                'field_id': settings.AMOCRM_FIELD_PRODUCT,
                'values':   [{'value': contact_form.product}],
            })

        if contact_form.referer:
            lead_custom_fields.append({
                'field_id': settings.AMOCRM_FIELD_REFERER,
                'values':   [{'value': contact_form.referer[:500]}],
            })

        lead_custom_fields.append({
            'field_id': settings.AMOCRM_FIELD_FORMID,
            'values':   [{'value': 'Заявка с сайта FAW.UZ'}],
        })

        if lead_name_override:
            lead_name = lead_name_override[:255]
        elif contact_form.product:
            lead_name = f"{contact_form.product} — {contact_form.name}"[:255]
        else:
            lead_name = f"Заявка с сайта: {contact_form.name}"[:255]

        is_bot_lead = bool(
            contact_form.referer and 'Telegram Bot' in contact_form.referer
        )
        base_tags = [] if is_bot_lead else [{'name': 'Сайт'}]
        base_tags.append({'name': 'FAW.UZ'})

        if contact_form.product:
            base_tags.append({'name': contact_form.product[:30]})
        if extra_tags:
            base_tags.extend({'name': t} for t in extra_tags)

        lead_dict = {
            'name':        lead_name,
            'price':       0,
            'pipeline_id': pipeline_id,
            'status_id':   status_id,
            'custom_fields_values': lead_custom_fields,
            '_embedded': {
                'tags': base_tags,
                'contacts': [{
                    'first_name': first_name,
                    'last_name':  last_name,
                    'custom_fields_values': [{
                        'field_code': 'PHONE',
                        'values': [{
                            'value':     contact_form.phone,
                            'enum_code': 'WORK',
                        }],
                    }],
                }],
            },
        }

        if contact_form.visitor_uid:
            lead_dict['visitor_uid'] = contact_form.visitor_uid

        return [lead_dict]

    @staticmethod
    def _resolve_lead_meta(contact_form) -> tuple[list[str], str | None]:
        referer = contact_form.referer or ''

        if 'Тест-драйв' in referer:
            tags = ['Тест-драйв', 'Telegram Bot']
            name = (
                f"Тест-драйв — {contact_form.product} — {contact_form.name}"
                if contact_form.product
                else f"Тест-драйв — {contact_form.name}"
            )
            return tags, name[:255]

        if 'Telegram Bot' in referer:
            utm_campaign = ''
            if contact_form.utm_data:
                try:
                    utm = json.loads(contact_form.utm_data)
                    utm_campaign = utm.get('utm_campaign', '')
                except Exception:
                    pass

            if utm_campaign == 'leasing':
                tags = ['Лизинг', 'Telegram Bot']
                name = (
                    f"Лизинг — {contact_form.product} — {contact_form.name}"
                    if contact_form.product
                    else f"Лизинг — {contact_form.name}"
                )
            elif utm_campaign == 'catalog_lead':
                tags = ['Каталог', 'Telegram Bot']
                name = (
                    f"{contact_form.product} — {contact_form.name}"
                    if contact_form.product
                    else f"Заявка из бота: {contact_form.name}"
                )
            else:
                tags = ['Telegram Bot']
                name = (
                    f"{contact_form.product} — {contact_form.name}"
                    if contact_form.product
                    else f"Заявка из бота: {contact_form.name}"
                )
            return tags, name[:255]

        return [], None