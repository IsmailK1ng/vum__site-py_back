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
            logger.info(f"🚀 Отправка лида в amoCRM: {lead_data.get('name', 'Без имени')}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=[lead_data],  # amoCRM принимает массив
                timeout=10
            )
            
            # Логируем запрос для отладки
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Request Headers: {self.headers}")
            logger.debug(f"Request Data: {[lead_data]}")
            logger.debug(f"Response Status: {response.status_code}")
            logger.debug(f"Response Body: {response.text}")
            
            response.raise_for_status()  # Вызовет ошибку если 4xx/5xx
            
            result = response.json()
            
            # ← ОТЛАДКА: Показываем что вернулось
            logger.info(f"📦 Ответ от amoCRM (type: {type(result).__name__})")
            
            # Извлекаем ID созданного лида
            if isinstance(result, list):
                # Если amoCRM вернул массив (старая версия API?)
                if len(result) > 0:
                    first_item = result[0]
                    if '_embedded' in first_item:
                        lead_id = first_item['_embedded']['leads'][0]['id']
                    elif 'id' in first_item:
                        lead_id = first_item['id']
                    else:
                        raise ValueError(f"Не найден ID лида в ответе: {first_item}")
                else:
                    raise ValueError("amoCRM вернул пустой массив")
                    
            elif isinstance(result, dict):
                # Правильный формат (объект с _embedded)
                if '_embedded' in result and 'leads' in result['_embedded']:
                    lead_id = result['_embedded']['leads'][0]['id']
                else:
                    raise ValueError(f"Не найден _embedded.leads в ответе: {result}")
            else:
                raise ValueError(f"Неожиданный тип ответа: {type(result)}")
            
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
            logger.error(f"Полный ответ: {response.text}")
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
                    return f"{errors[0].get('code', 'unknown')}: {errors[0].get('detail', 'Unknown error')}"
            
            # Общая ошибка
            if 'detail' in error_data:
                return error_data['detail']
            
            if 'title' in error_data:
                return error_data['title']
            
            return response.text[:200]
            
        except Exception:
            return response.text[:200]