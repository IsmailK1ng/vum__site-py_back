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
            logger.info(f"⏭️ Лид #{contact_form.id} уже отправлен (amoCRM ID: {contact_form.amocrm_lead_id})")
            return

        try:
            # Получаем токен
            token_obj = AmoCRMToken.get_instance()

            if token_obj.is_expired():
                TokenManager.refresh_token(token_obj)
                token_obj.refresh_from_db()

            # Выбираем pipeline_id (из настроек) и получаем первый редактируемый статус в этой воронке
            pipeline_id = settings.AMOCRM_PIPELINE_ID
            editable_status = cls._get_editable_status_for_pipeline(token_obj.access_token, pipeline_id)
            if editable_status:
                status_to_use = editable_status
                logger.debug(f"Выбран редактируемый статус {status_to_use} для pipeline {pipeline_id}")
            else:
                status_to_use = settings.AMOCRM_STATUS_ID
                logger.warning(f"Редактируемый статус не найден — используем fallback {status_to_use}")

            # Подготовка данных (передаём pipeline_id и status_to_use)
            lead_data = cls._prepare_lead_data(contact_form, pipeline_id, status_to_use)

            headers = {
                'Authorization': f'Bearer {token_obj.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/complex',
                json=lead_data,
                headers=headers,
                timeout=10
            )

            # Логируем полный ответ для отладки (можно опустить позже)
            try:
                logger.debug(f"amoCRM response: {response.status_code} {response.json()}")
            except Exception:
                logger.debug(f"amoCRM response (non-json): {response.status_code} {response.text[:500]}")

            # Обработка ответа
            if response.status_code in [200, 201]:
                result = response.json()
                lead_id = cls._extract_lead_id(result)

                if lead_id:
                    contact_form.amocrm_status = 'sent'
                    contact_form.amocrm_lead_id = lead_id
                    contact_form.amocrm_sent_at = timezone.now()
                    contact_form.amocrm_error = None
                    contact_form.save()
                    logger.info(f"✅ Лид #{contact_form.id} отправлен (amoCRM ID: {lead_id})")
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
            logger.error(f"💥 Критическая ошибка: {error_text}")
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()

    @staticmethod
    def _get_editable_status_for_pipeline(access_token, pipeline_id):
        """
        Возвращает первый is_editable=True status_id для pipeline, иначе None.
        """
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

        # Регион
        lead_custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_REGION,
            "values": [{"value": contact_form.get_region_display()}]
        })

        # Сообщение (с обрезкой)
        if contact_form.message:
            msg = contact_form.message.strip()
            if len(msg) > 1000:
                msg = msg[:997] + "..."
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_MESSAGE,
                "values": [{"value": msg}]
            })

        # Модель техники
        if contact_form.product:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_PRODUCT,
                "values": [{"value": contact_form.product}]
            })

        # Referer
        if contact_form.referer:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_REFERER,
                "values": [{"value": contact_form.referer[:500]}]
            })

        # UTM
        if contact_form.utm_data:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_UTM,
                "values": [{"value": contact_form.utm_data[:1000]}]
            })

        # ID формы — по-человечески
        lead_custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_FORMID,
            "values": [{"value": "Заявка с сайта FAW.UZ"}]
        })

        # Название лида
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

        # visitor_uid
        if contact_form.visitor_uid:
            lead_dict["visitor_uid"] = contact_form.visitor_uid
            logger.info(f"visitor_uid добавлен: {contact_form.visitor_uid}")
        else:
            logger.warning(f"visitor_uid отсутствует для лида #{contact_form.id}")

        # Тег с моделью (опционально)
        if contact_form.product:
            lead_dict["_embedded"]["tags"].append({"name": contact_form.product[:30]})

        return [lead_dict]