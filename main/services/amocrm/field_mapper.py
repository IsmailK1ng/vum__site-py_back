# main/services/amocrm/field_mapper.py

from django.conf import settings


def map_contact_form_to_amocrm(contact_form):
    """
    Преобразовать ContactForm → JSON для amoCRM API
    """
    
    # Название лида
    if contact_form.product:
        lead_name = f"{contact_form.product} — {contact_form.name}"
    else:
        lead_name = f"Заявка от {contact_form.name}"
    
    if contact_form.region:
        lead_name += f" ({contact_form.get_region_display()})"
    
    # Разделяем имя
    name_parts = contact_form.name.strip().split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Кастомные поля
    custom_fields = [
        {
            "field_id": settings.AMOCRM_FIELD_FORMNAME,
            "values": [{"value": "Контактная форма FAW.UZ"}]
        },
        {
            "field_id": settings.AMOCRM_FIELD_FORMID,
            "values": [{"value": "contact-form-uz"}]
        },
        {
            "field_id": settings.AMOCRM_FIELD_REGION,
            "values": [{"value": contact_form.get_region_display()}]
        },
    ]
    
    # Модель техники
    if contact_form.product:
        custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_PRODUCT,
            "values": [{"value": contact_form.product}]
        })
    
    # ← ДОБАВЬ REFERER
    if contact_form.referer:
        custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_REFERER,
            "values": [{"value": contact_form.referer}]
        })
    
    # ← ДОБАВЬ UTM_ID
    if contact_form.utm_data:
        custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_UTM,
            "values": [{"value": contact_form.utm_data}]
        })
    
    # Формируем данные для amoCRM
    lead_data = {
        "name": lead_name,
        "price": 0,
        "pipeline_id": settings.AMOCRM_PIPELINE_ID,
        "status_id": settings.AMOCRM_STATUS_ID,
        "custom_fields_values": custom_fields,
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
    
    return lead_data