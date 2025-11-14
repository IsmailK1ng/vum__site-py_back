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
        """
        Отправка лида в amoCRM через /leads/complex
        
        Args:
            contact_form: Объект ContactForm
        """
        # Пропускаем если уже отправлено
        if contact_form.amocrm_status == 'sent' and contact_form.amocrm_lead_id:
            logger.info(f"⏭️  Лид #{contact_form.id} уже отправлен (ID: {contact_form.amocrm_lead_id})")
            return
        
        try:
            # Получаем валидный токен
            token_obj = AmoCRMToken.get_instance()
            
            if token_obj.is_expired():
                logger.info("🔄 Токен истекает, обновляем...")
                TokenManager.refresh_token(token_obj)
                token_obj.refresh_from_db()
            
            # Подготавливаем данные
            lead_data = cls._prepare_lead_data(contact_form)
            
            # Заголовки
            headers = {
                'Authorization': f'Bearer {token_obj.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Логируем отправку
            lead_name = lead_data[0].get('name', 'Без имени')
            logger.info(f"🚀 Отправка лида в amoCRM: {lead_name}")
            
            # Отправляем
            response = requests.post(
                f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/complex',
                json=lead_data,
                headers=headers,
                timeout=10
            )
            
            # Обработка ответа
            if response.status_code in [200, 201]:
                result = response.json()
                
                # Извлекаем ID лида
                lead_id = cls._extract_lead_id(result)
                
                if lead_id:
                    contact_form.amocrm_status = 'sent'
                    contact_form.amocrm_lead_id = lead_id
                    contact_form.amocrm_sent_at = timezone.now()
                    contact_form.amocrm_error = None
                    contact_form.save()
                    
                    logger.info(f"✅ Лид успешно создан. ID: {lead_id}")
                else:
                    raise ValueError("Не удалось извлечь ID лида из ответа")
                
            else:
                error_text = cls._parse_error_response(response)
                logger.error(f"❌ Ошибка HTTP {response.status_code}: {error_text}")
                
                contact_form.amocrm_status = 'failed'
                contact_form.amocrm_error = error_text[:500]
                contact_form.save()
                
        except requests.exceptions.Timeout:
            error_text = "Таймаут соединения с amoCRM"
            logger.error(f"❌ {error_text}")
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text
            contact_form.save()
            
        except requests.exceptions.RequestException as e:
            error_text = f"Ошибка запроса: {str(e)}"
            logger.error(f"❌ {error_text}")
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()
            
        except Exception as e:
            error_text = f"{type(e).__name__}: {str(e)}"
            logger.error(f"❌ Неожиданная ошибка: {error_text}")
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()
    
    @staticmethod
    def _extract_lead_id(result):
        """
        Извлечь ID лида из ответа amoCRM
        
        Ответ может быть в двух форматах:
        1. [{"id": 123, ...}]
        2. [{"_embedded": {"leads": [{"id": 123}]}}]
        """
        try:
            if isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                
                # Формат 1: прямой ID
                if 'id' in first_item:
                    return first_item['id']
                
                # Формат 2: вложенный в _embedded
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
        """Извлечь текст ошибки из ответа amoCRM"""
        try:
            error_data = response.json()
            
            # Ошибки валидации (422)
            if 'validation-errors' in error_data:
                errors = error_data['validation-errors']
                if len(errors) > 0 and 'errors' in errors[0]:
                    first_error = errors[0]['errors'][0]
                    code = first_error.get('code', 'unknown')
                    detail = first_error.get('detail', 'Unknown error')
                    return f"{code}: {detail}"
            
            # Общая ошибка
            if 'detail' in error_data:
                return error_data['detail']
            
            if 'title' in error_data:
                return error_data['title']
            
            return response.text[:200]
            
        except Exception:
            return response.text[:200]
    
    @staticmethod
    def _prepare_lead_data(contact_form):
        """
        Подготовить данные лида для отправки в amoCRM
        
        ВАЖНО: Использует ID полей из settings.py
        """
        # Разделяем имя
        name_parts = contact_form.name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # ========== КАСТОМНЫЕ ПОЛЯ ЛИДА ==========
        lead_custom_fields = [
            {
                "field_id": settings.AMOCRM_FIELD_REGION,
                "values": [{"value": contact_form.get_region_display()}]
            }
        ]
        
        # Сообщение (если есть)
        if contact_form.message:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_FORMNAME,  
                "values": [{"value": contact_form.message}]
            })
        
        # Продукт
        if contact_form.product:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_PRODUCT,
                "values": [{"value": contact_form.product}]
            })
        
        # Referer
        if contact_form.referer:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_REFERER,
                "values": [{"value": contact_form.referer}]
            })
        
        # UTM данные
        if contact_form.utm_data:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_UTM,
                "values": [{"value": contact_form.utm_data}]
            })
        
        # FormID (идентификатор формы)
        lead_custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_FORMID,
            "values": [{"value": "contact-form-faw-uz"}]
        })
        
        # ========== НАЗВАНИЕ ЛИДА ==========
        lead_name = f"Заявка с сайта: {contact_form.name}"
        if contact_form.product:
            lead_name = f"{contact_form.product} — {contact_form.name}"
        
        # ========== ФОРМИРУЕМ СТРУКТУРУ ==========
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