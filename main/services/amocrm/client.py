# main/services/amocrm/client.py

import requests
import logging
from django.conf import settings

logger = logging.getLogger('amocrm')


class AmoCRMClient:
    """Клиент для работы с amoCRM API"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4"
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def create_lead(self, lead_data):
        """
        Создать лид через /leads/complex
        
        Args:
            lead_data (dict): Данные лида в формате amoCRM
            
        Returns:
            dict: {'success': bool, 'lead_id': str/None, 'error': str/None}
        """
        url = f"{self.base_url}/leads/complex"
        
        try:
            # ✅ МИНИМАЛЬНОЕ ЛОГИРОВАНИЕ (только название лида)
            lead_name = lead_data.get('name', 'Без имени')
            logger.info(f"🚀 Отправка лида в amoCRM: {lead_name}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=[lead_data],  # amoCRM принимает массив
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Извлекаем ID созданного лида
            if isinstance(result, list):
                if len(result) > 0:
                    first_item = result[0]
                    if '_embedded' in first_item:
                        lead_id = first_item['_embedded']['leads'][0]['id']
                    elif 'id' in first_item:
                        lead_id = first_item['id']
                    else:
                        raise ValueError("Lead ID not found in response")
                else:
                    raise ValueError("Empty response from amoCRM")
                    
            elif isinstance(result, dict):
                if '_embedded' in result and 'leads' in result['_embedded']:
                    lead_id = result['_embedded']['leads'][0]['id']
                else:
                    raise ValueError("Lead ID not found in response")
            else:
                raise ValueError(f"Unexpected response type: {type(result)}")
            
            logger.info(f"✅ Лид успешно создан. ID: {lead_id}")
            
            return {
                'success': True,
                'lead_id': str(lead_id),
                'error': None
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = self._parse_error(response)
            logger.error(f"❌ Ошибка HTTP {response.status_code}: {error_msg}")
            
            return {
                'success': False,
                'lead_id': None,
                'error': f"HTTP {response.status_code}: {error_msg}"
            }
            
        except requests.exceptions.Timeout:
            logger.error("❌ Таймаут соединения с amoCRM")
            return {
                'success': False,
                'lead_id': None,
                'error': "Таймаут соединения с amoCRM"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка запроса: {str(e)}")
            return {
                'success': False,
                'lead_id': None,
                'error': f"Ошибка запроса: {str(e)}"
            }
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"❌ Ошибка парсинга ответа: {str(e)}")
            return {
                'success': False,
                'lead_id': None,
                'error': f"Ошибка парсинга ответа: {str(e)}"
            }
    
    def _parse_error(self, response):
        """Извлечь текст ошибки из ответа amoCRM"""
        try:
            error_data = response.json()
            
            # Ошибки валидации (422)
            if 'validation-errors' in error_data:
                errors = error_data['validation-errors'][0].get('errors', [])
                if errors:
                    code = errors[0].get('code', 'unknown')
                    detail = errors[0].get('detail', 'Unknown error')
                    return f"{code}: {detail}"
            
            # Общая ошибка
            if 'detail' in error_data:
                return error_data['detail']
            
            if 'title' in error_data:
                return error_data['title']
            
            return response.text[:200]
            
        except Exception:
            return response.text[:200]
    
    def get_custom_fields(self, entity_type='leads'):
        """
        Получить список кастомных полей
        
        Args:
            entity_type (str): Тип сущности ('leads', 'contacts', 'companies')
            
        Returns:
            list: Список полей с их ID и названиями
        """
        url = f"{self.base_url}/{entity_type}/custom_fields"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            if '_embedded' in result and 'custom_fields' in result['_embedded']:
                return result['_embedded']['custom_fields']
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения полей: {str(e)}")
            return []