# main/services/amocrm/field_mapper.py

from django.conf import settings


def map_contact_form_to_amocrm(contact_form):
    """
    Преобразовать ContactForm → JSON для amoCRM API
    
    Args:
        contact_form: Объект модели ContactForm
        
    Returns:
        dict: Данные в формате amoCRM
    """
    
    # Имя лида (заголовок сделки)
    lead_name = f"Заявка от {contact_form.name}"
    if contact_form.region:
        lead_name += f" ({contact_form.get_region_display()})"
    
    # Разделяем имя на first_name и last_name
    name_parts = contact_form.name.strip().split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Формируем данные для amoCRM
    lead_data = {
        "name": lead_name,
        "price": 0,  # Бюджет (можно оставить 0)
        "pipeline_id": settings.AMOCRM_PIPELINE_ID,
        "status_id": settings.AMOCRM_STATUS_ID,
        
        # Кастомные поля
        "custom_fields_values": [
            # Название формы
            {
                "field_id": settings.AMOCRM_FIELD_FORMNAME,
                "values": [{"value": "Контактная форма FAW.UZ"}]
            },
            # ID формы
            {
                "field_id": settings.AMOCRM_FIELD_FORMID,
                "values": [{"value": "contact-form-uz"}]
            },
            # Регион
            {
                "field_id": settings.AMOCRM_FIELD_REGION,
                "values": [{"value": contact_form.get_region_display()}]
            },
        ],
        
        # Встроенные объекты
        "_embedded": {
            "tags": [
                {"name": "Сайт"},
                {"name": "FAW.UZ"}
            ],
            
            # Контакт (клиент)
            "contacts": [
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "custom_fields_values": [
                        # Телефон
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
    
    # Добавляем сообщение в примечание (опционально)
    if contact_form.message:
        # Примечание добавляется через отдельное поле или API notes
        # Для простоты можно добавить в название
        pass
    
    return lead_data