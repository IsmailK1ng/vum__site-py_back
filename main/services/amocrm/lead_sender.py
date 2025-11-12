# main/services/amocrm/lead_sender.py

from django.utils import timezone
from .token_manager import TokenManager
from .client import AmoCRMClient
from .field_mapper import map_contact_form_to_amocrm


def send_contact_form_to_amocrm(contact_form):
    """
    Отправить ContactForm в amoCRM
    
    Args:
        contact_form: Объект модели ContactForm
        
    Returns:
        dict: {'success': bool, 'lead_id': str/None, 'error': str/None}
    """
    try:
        access_token = TokenManager.get_valid_token()
        client = AmoCRMClient(access_token)
        lead_data = map_contact_form_to_amocrm(contact_form)
        result = client.create_lead(lead_data)
        
        if result['success']:
            contact_form.amocrm_status = 'sent'
            contact_form.amocrm_lead_id = result['lead_id']
            contact_form.amocrm_sent_at = timezone.now()
            contact_form.amocrm_error = None
        else:
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = result['error']
        
        contact_form.save()
        return result
        
    except Exception as e:
        contact_form.amocrm_status = 'failed'
        contact_form.amocrm_error = str(e)
        contact_form.save()
        
        return {
            'success': False,
            'lead_id': None,
            'error': str(e)
        }