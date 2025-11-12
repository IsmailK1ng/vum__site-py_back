# main/services/amocrm/lead_sender.py

import logging
from django.utils import timezone
from .token_manager import TokenManager
from .client import AmoCRMClient
from .field_mapper import map_contact_form_to_amocrm

logger = logging.getLogger('amocrm')


def send_contact_form_to_amocrm(contact_form):
    """
    Отправить ContactForm в amoCRM
    
    Args:
        contact_form: Объект модели ContactForm
        
    Returns:
        dict: {'success': bool, 'lead_id': str/None, 'error': str/None}
    """
    try:
        # 1. Получить валидный токен (обновится автоматически если нужно)
        access_token = TokenManager.get_valid_token()
        
        # 2. Создать API клиент
        client = AmoCRMClient(access_token)
        
        # 3. Преобразовать данные формы → JSON для amoCRM
        lead_data = map_contact_form_to_amocrm(contact_form)
        
        # 4. Отправить в amoCRM
        result = client.create_lead(lead_data)
        
        # 5. Обновить статус в БД
        if result['success']:
            contact_form.amocrm_status = 'sent'
            contact_form.amocrm_lead_id = result['lead_id']
            contact_form.amocrm_sent_at = timezone.now()
            contact_form.amocrm_error = None
            logger.info(f"✅ Лид {contact_form.id} успешно отправлен. amoCRM ID: {result['lead_id']}")
        else:
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = result['error']
            logger.error(f"❌ Лид {contact_form.id} не отправлен: {result['error']}")
        
        contact_form.save()
        
        return result
        
    except Exception as e:
        # Критическая ошибка (например, токены не настроены)
        error_msg = f"Критическая ошибка: {str(e)}"
        logger.exception(f"❌ {error_msg}")
        
        contact_form.amocrm_status = 'failed'
        contact_form.amocrm_error = error_msg
        contact_form.save()
        
        return {
            'success': False,
            'lead_id': None,
            'error': error_msg
        }