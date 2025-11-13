import requests
import logging
from django.utils import timezone
from main.models import AmoCRMToken
from main.services.amocrm.token_manager import TokenManager

logger = logging.getLogger('amocrm')


class LeadSender:
    """Отправка лидов в amoCRM"""
    
    @classmethod
    def send_lead(cls, contact_form):
        """
        Отправить лид в amoCRM
        ВАЖНО: ТОЛЬКО 1 ПОПЫТКА, БЕЗ СТАТУСА 'PENDING'
        """

        
        # Пропускаем уже отправленные
        if contact_form.amocrm_status == 'sent' and contact_form.amocrm_lead_id:
            logger.info(f"Лид #{contact_form.id} уже отправлен (ID: {contact_form.amocrm_lead_id})")
            return
        
        try:
            # Получаем токен
            token_obj = AmoCRMToken.get_instance()
            
            # Обновляем токен если нужно
            if token_obj.is_expired():
                logger.info("Токен истекает, обновляем...")
                TokenManager.refresh_token(token_obj)
                token_obj.refresh_from_db()
            
            # Подготовка данных
            lead_data = cls._prepare_lead_data(contact_form)
            
            # Отправка (ИСПОЛЬЗУЕМ /leads/complex!)
            headers = {
                'Authorization': f'Bearer {token_obj.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://fawtrucks.amocrm.ru/api/v4/leads/complex', 
                json=lead_data,
                headers=headers,
                timeout=10
            )
            
            # ПРОВЕРКА ОТВЕТА
            if response.status_code in [200, 201]:
                result = response.json()
                
                # Парсим ответ от /complex
                if isinstance(result, list) and len(result) > 0:
                    lead_id = result[0]['id']
                else:
                    lead_id = result['_embedded']['leads'][0]['id']
                
                # УСПЕХ
                contact_form.amocrm_status = 'sent'
                contact_form.amocrm_lead_id = lead_id
                contact_form.amocrm_sent_at = timezone.now()
                contact_form.amocrm_error = None
                contact_form.save()
                
                logger.info(f"Лид #{contact_form.id} успешно отправлен (amoCRM ID: {lead_id})")
                
            else:
                # ОШИБКА
                error_text = f"HTTP {response.status_code}: {response.text[:500]}"
                
                contact_form.amocrm_status = 'failed'
                contact_form.amocrm_error = error_text
                contact_form.save()
                
                logger.error(f"Ошибка отправки лида #{contact_form.id}: {error_text}")
                
        except Exception as e:
            # КРИТИЧЕСКАЯ ОШИБКА
            error_text = f"{type(e).__name__}: {str(e)}"
            
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()
            
            logger.error(f"Критическая ошибка отправки лида #{contact_form.id}: {error_text}")
    
    @staticmethod
    def _prepare_lead_data(contact_form):
        """Подготовка данных лида для amoCRM"""
        
        # Разделяем имя на части
        name_parts = contact_form.name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Формируем кастомные поля ЛИДА
        lead_custom_fields = [
            {
                "field_id": 3027829,  # REGION
                "values": [{"value": contact_form.region}]
            },
            {
                "field_id": 2944145,  # TEXTAREA (сообщение)
                "values": [{"value": contact_form.message}]
            }
        ]
        
        # Добавляем referer если есть
        if contact_form.referer:
            lead_custom_fields.append({
                "field_id": 3022633,  # REFERER
                "values": [{"value": contact_form.referer}]
            })
        
        # Добавляем UTM данные если есть
        if contact_form.utm_data:
            lead_custom_fields.append({
                "field_id": 3024889,  # UTM_ID
                "values": [{"value": contact_form.utm_data}]
            })
        
        return [
            {
                "name": f"Заявка с сайта: {contact_form.name}",
                "price": 0,
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