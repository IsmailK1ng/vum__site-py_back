"""
Модуль для проверки Google reCAPTCHA v3 токенов
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_recaptcha(token, action='submit', remote_ip=None):
    """
    Проверяет reCAPTCHA токен через Google API
    
    Args:
        token (str): Токен от клиента
        action (str): Ожидаемое действие (submit, login и т.д.)
        remote_ip (str): IP адрес клиента (опционально)
    
    Returns:
        dict: {
            'success': bool,
            'score': float или None,
            'action': str,
            'error': str или None
        }
    """
    
    # Если reCAPTCHA выключена
    if not settings.RECAPTCHA_ENABLED:
        logger.debug("reCAPTCHA disabled, skipping verification")
        return {
            'success': True,
            'score': None,
            'action': action,
            'error': None
        }
    
    # Проверка наличия токена
    if not token:
        logger.critical(f"🚨 reCAPTCHA TOKEN MISSING! action={action}, token={repr(token)}")
        return {
            'success': False,
            'score': None,
            'action': action,
            'error': 'Token is required'
        }
    
    # Подготовка данных для Google API
    payload = {
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': token
    }
    
    if remote_ip:
        payload['remoteip'] = remote_ip
    
    try:
        # Отправляем запрос в Google
        response = requests.post(
            settings.RECAPTCHA_VERIFY_URL,
            data=payload,
            timeout=5
        )
        
        result = response.json()
        
        # Логируем ответ
        logger.info(f"✅ reCAPTCHA API Response: success={result.get('success')}, score={result.get('score')}, action={result.get('action')}")
        
        # Проверяем успешность
        if not result.get('success'):
            error_codes = result.get('error-codes', [])
            logger.error(f"❌ reCAPTCHA API Error: {error_codes}, token_exists={bool(token)}, action={action}")
            return {
                'success': False,
                'score': None,
                'action': result.get('action'),
                'error': f"Verification failed: {', '.join(error_codes)}"
            }
        
        # Проверяем action (опционально)
        if action and result.get('action') != action:
            logger.warning(f"Action mismatch: expected {action}, got {result.get('action')}")
        
        # Проверяем score
        score = result.get('score', 0)
        threshold = getattr(settings, 'RECAPTCHA_SCORE_THRESHOLD', 0.3)  # Снижено с 0.5 на 0.3
        
        logger.info(f"🔍 reCAPTCHA Score Check: {score} >= {threshold}? Action: {result.get('action')}")
        
        if score < threshold:
            logger.warning(f"⚠️ Low reCAPTCHA score: {score} < {threshold} (Action: {result.get('action')})")
            return {
                'success': False,
                'score': score,
                'action': result.get('action'),
                'error': f'Suspicious activity detected (score: {score})'
            }
        
        # Всё ОК
        return {
            'success': True,
            'score': score,
            'action': result.get('action'),
            'error': None
        }
    
    except requests.RequestException as e:
        logger.error(f"reCAPTCHA API request failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'score': None,
            'action': action,
            'error': 'Service temporarily unavailable'
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in reCAPTCHA verification: {str(e)}", exc_info=True)
        return {
            'success': False,
            'score': None,
            'action': action,
            'error': 'Internal error'
        }


def get_client_ip(request):
    """
    Получает реальный IP адрес клиента (с учётом прокси)
    
    Args:
        request: Django request объект
    
    Returns:
        str: IP адрес
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip