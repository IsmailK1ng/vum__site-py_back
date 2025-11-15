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
        """Отправка лида в amoCRM через /leads/complex"""
        if contact_form.amocrm_status == 'sent' and contact_form.amocrm_lead_id:
            return
        
        try:
            token_obj = AmoCRMToken.get_instance()
            
            if token_obj.is_expired():
                TokenManager.refresh_token(token_obj)
                token_obj.refresh_from_db()
            
            lead_data = cls._prepare_lead_data(contact_form)
            
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
            
            if response.status_code in [200, 201]:
                result = response.json()
                lead_id = cls._extract_lead_id(result)
                
                if lead_id:
                    contact_form.amocrm_status = 'sent'
                    contact_form.amocrm_lead_id = lead_id
                    contact_form.amocrm_sent_at = timezone.now()
                    contact_form.amocrm_error = None
                    contact_form.save()
                    logger.info(f"Лид #{contact_form.id} отправлен (amoCRM ID: {lead_id})")
                else:
                    raise ValueError("ID лида не найден в ответе")
            else:
                error_text = cls._parse_error_response(response)
                logger.error(f"Ошибка amoCRM {response.status_code}: {error_text}")
                contact_form.amocrm_status = 'failed'
                contact_form.amocrm_error = error_text[:500]
                contact_form.save()
                
        except requests.exceptions.Timeout:
            error_text = "Таймаут соединения с amoCRM"
            logger.error(error_text)
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text
            contact_form.save()
            
        except requests.exceptions.RequestException as e:
            error_text = f"Ошибка запроса: {str(e)}"
            logger.error(error_text)
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()
            
        except Exception as e:
            error_text = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Критическая ошибка: {error_text}")
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()
    
    @staticmethod
    def _extract_lead_id(result):
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
            logger.error(f"Ошибка парсинга ID: {str(e)}")
            return None
    
    @staticmethod
    def _parse_error_response(response):
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
    def _prepare_lead_data(contact_form):
        name_parts = contact_form.name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        lead_custom_fields = [
            {
                "field_id": settings.AMOCRM_FIELD_REGION,
                "values": [{"value": contact_form.get_region_display()}]
            }
        ]
        
        if contact_form.message:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_FORMNAME,
                "values": [{"value": contact_form.message}]
            })
        
        if contact_form.product:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_PRODUCT,
                "values": [{"value": contact_form.product}]
            })
        
        if contact_form.referer:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_REFERER,
                "values": [{"value": contact_form.referer}]
            })
        
        if contact_form.utm_data:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_UTM,
                "values": [{"value": contact_form.utm_data}]
            })
        
        lead_custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_FORMID,
            "values": [{"value": "contact-form-faw-uz"}]
        })
        
        lead_name = f"Заявка с сайта: {contact_form.name}"
        if contact_form.product:
            lead_name = f"{contact_form.product} — {contact_form.name}"
        
        return [
            {
                "name": lead_name,
                "price": 0,
                "pipeline_id": settings.AMOCRM_PIPELINE_ID,
                "status_id": settings.AMOCRM_STATUS_ID,
                "custom_fields_values": lead_custom_fields,
                "_embedded": {
                    "tags": [
                        {"name": "Сайт"},
                        {"name": "FAW.UZ"}
                    ],
                    "contacts": [
                        {
                            "first_name": first_name,
                            "last_name": last_name,
                            "custom_fields_values": [
                                {
                                    "field_code": "PHONE",
                                    "values": [
                                        {
                                            "value": contact_form.phone,
                                            "enum_code": "WORK"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        ]