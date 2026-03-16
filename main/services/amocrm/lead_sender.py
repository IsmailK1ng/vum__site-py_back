import json
import requests
import logging
from django.utils import timezone
from django.conf import settings
from main.models import AmoCRMToken
from main.services.amocrm.token_manager import TokenManager

logger = logging.getLogger('amocrm')


class LeadSender:

    @classmethod
    def send_lead(cls, contact_form):
        """Отправка лида в amoCRM"""
        if contact_form.amocrm_status == 'sent' and contact_form.amocrm_lead_id:
            return

        try:
            token_obj = AmoCRMToken.get_instance()

            if token_obj.is_expired():
                TokenManager.refresh_token(token_obj)
                token_obj.refresh_from_db()

            pipeline_id = settings.AMOCRM_PIPELINE_ID
            editable_status = cls._get_editable_status_for_pipeline(token_obj.access_token, pipeline_id)
            status_to_use = editable_status if editable_status else settings.AMOCRM_STATUS_ID

            lead_data = cls._prepare_lead_data(contact_form, pipeline_id, status_to_use)

            headers = {
                'Authorization': f'Bearer {token_obj.access_token}',
                'Content-Type': 'application/json'
            }

            # Шаг 1 — создаём лид
            response = requests.post(
                f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/complex',
                json=lead_data,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                result = response.json()
                lead_id = cls._extract_lead_id(result)

                if lead_id:
                    contact_form.amocrm_status = 'sent'
                    contact_form.amocrm_lead_id = lead_id
                    contact_form.amocrm_sent_at = timezone.now()
                    contact_form.amocrm_error = None
                    contact_form.save()

                    # Шаг 2 — PATCH для UTM полей виджета статистики
                    cls._patch_utm_fields(lead_id, contact_form, headers)

                else:
                    raise ValueError("ID лида не найден в ответе amoCRM")
            else:
                error_text = cls._parse_error_response(response)
                logger.error(f"❌ Ошибка amoCRM {response.status_code}: {error_text}")
                contact_form.amocrm_status = 'failed'
                contact_form.amocrm_error = error_text[:500]
                contact_form.save()

        except requests.exceptions.Timeout:
            error_text = "Таймаут соединения с amoCRM"
            logger.error(f"⏱️ {error_text}")
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text
            contact_form.save()

        except requests.exceptions.RequestException as e:
            error_text = f"Ошибка запроса: {str(e)}"
            logger.error(f"🌐 {error_text}")
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()

        except Exception as e:
            error_text = f"{type(e).__name__}: {str(e)}"
            logger.error(f"💥 Критическая ошибка: {error_text}", exc_info=True)
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()

    @classmethod
    def _patch_utm_fields(cls, lead_id, contact_form, headers):
        """PATCH запрос для заполнения UTM полей виджета статистики"""
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

        custom_fields = []
        for key, field_id in utm_field_map.items():
            value = (utm.get(key) or '').strip()
            if value:
                custom_fields.append({
                    "field_id": field_id,
                    "values": [{"value": value[:500]}]
                })

        if not custom_fields:
            return

        try:
            response = requests.patch(
                f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/{lead_id}',
                headers=headers,
                json={"custom_fields_values": custom_fields},
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"✅ UTM поля обновлены для лида {lead_id}")
            else:
                logger.error(f"❌ Ошибка PATCH UTM лид {lead_id}: {response.status_code} {response.text[:200]}")
        except Exception as e:
            logger.error(f"❌ Исключение PATCH UTM лид {lead_id}: {str(e)}")

    @staticmethod
    def _get_editable_status_for_pipeline(access_token, pipeline_id):
        """Возвращает первый is_editable=True status_id для pipeline"""
        try:
            url = f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/pipelines/{pipeline_id}/statuses'
            headers = {'Authorization': f'Bearer {access_token}'}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            statuses = data.get('_embedded', {}).get('statuses', [])
            for s in statuses:
                if s.get('is_editable', False):
                    return s.get('id')
            return None
        except Exception as e:
            logger.error(f"Не удалось получить статусы pipeline {pipeline_id}: {e}")
            return None

    @staticmethod
    def _extract_lead_id(result):
        """Извлечение ID лида из ответа amoCRM"""
        try:
            if isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                if 'id' in first_item:
                    return first_item['id']
                if '_embedded' in first_item and 'leads' in first_item['_embedded']:
                    leads = first_item['_embedded']['leads']
                    if len(leads) > 0:
                        return leads[0]['id']
            return None
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"❌ Ошибка парсинга ID лида: {str(e)}")
            return None

    @staticmethod
    def _parse_error_response(response):
        """Парсинг текста ошибки из ответа amoCRM"""
        try:
            error_data = response.json()
            if 'validation-errors' in error_data:
                errors = error_data['validation-errors']
                if len(errors) > 0 and 'errors' in errors[0]:
                    first_error = errors[0]['errors'][0]
                    return f"{first_error.get('code')}: {first_error.get('detail')}"
            if 'detail' in error_data:
                return error_data['detail']
            if 'title' in error_data:
                return error_data['title']
            return response.text[:200]
        except Exception:
            return response.text[:200]

    @staticmethod
    def _prepare_lead_data(contact_form, pipeline_id, status_id):
        """Подготовка данных лида для отправки в amoCRM"""
        name_parts = contact_form.name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        lead_custom_fields = []

        lead_custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_REGION,
            "values": [{"value": contact_form.get_region_display()}]
        })

        if contact_form.message:
            msg = contact_form.message.strip()
            if len(msg) > 1000:
                msg = msg[:997] + "..."
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_MESSAGE,
                "values": [{"value": msg}]
            })

        if contact_form.product:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_PRODUCT,
                "values": [{"value": contact_form.product}]
            })

        if contact_form.referer:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_REFERER,
                "values": [{"value": contact_form.referer[:500]}]
            })

        lead_custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_FORMID,
            "values": [{"value": "Заявка с сайта FAW.UZ"}]
        })

        lead_name = f"{contact_form.product} — {contact_form.name}" if contact_form.product else f"Заявка с сайта: {contact_form.name}"

        lead_dict = {
            "name": lead_name,
            "price": 0,
            "pipeline_id": pipeline_id,
            "status_id": status_id,
            "custom_fields_values": lead_custom_fields,
            "_embedded": {
                "tags": [{"name": "Сайт"}, {"name": "FAW.UZ"}],
                "contacts": [{
                    "first_name": first_name,
                    "last_name": last_name,
                    "custom_fields_values": [{
                        "field_code": "PHONE",
                        "values": [{
                            "value": contact_form.phone,
                            "enum_code": "WORK"
                        }]
                    }]
                }]
            }
        }

        if contact_form.visitor_uid:
            lead_dict["visitor_uid"] = contact_form.visitor_uid

        if contact_form.product:
            lead_dict["_embedded"]["tags"].append({"name": contact_form.product[:30]})

        return [lead_dict]