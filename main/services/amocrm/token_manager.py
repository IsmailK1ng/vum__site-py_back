import requests
import logging
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from main.models import AmoCRMToken

logger = logging.getLogger('amocrm')


class TokenManager:
    """Управление токенами amoCRM"""
    
    @staticmethod
    def get_valid_token():
        """Получить валидный access_token"""
        token_obj = AmoCRMToken.get_instance()
        
        if not token_obj.access_token or not token_obj.refresh_token:
            logger.error("❌ Токены не найдены в БД! Запустите команду init_amocrm_tokens") 
            raise Exception("amoCRM токены не настроены")
        
        if token_obj.is_expired():
            TokenManager.refresh_token(token_obj)
        
        return token_obj.access_token
    
    @staticmethod
    def refresh_token(token_obj):
        """Обновить access_token через refresh_token"""
        url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/oauth2/access_token"
        
        data = {
            "client_id": settings.AMOCRM_CLIENT_ID,
            "client_secret": settings.AMOCRM_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": token_obj.refresh_token,
            "redirect_uri": settings.AMOCRM_REDIRECT_URI,
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            token_obj.access_token = result['access_token']
            token_obj.refresh_token = result['refresh_token']
            token_obj.expires_at = timezone.now() + timedelta(seconds=result['expires_in'])
            token_obj.save()

            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка обновления токена: {str(e)}", exc_info=True) 
            raise Exception(f"Не удалось обновить токен: {str(e)}")
    
    @staticmethod
    def save_initial_tokens(access_token, refresh_token, expires_in):
        """Сохранить токены после первичной авторизации"""
        token_obj = AmoCRMToken.get_instance()
        token_obj.access_token = access_token
        token_obj.refresh_token = refresh_token
        token_obj.expires_at = timezone.now() + timedelta(seconds=expires_in)
        token_obj.save()
