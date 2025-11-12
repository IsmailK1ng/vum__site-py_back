# main/services/amocrm/__init__.py

from .lead_sender import send_contact_form_to_amocrm

__all__ = ['send_contact_form_to_amocrm']