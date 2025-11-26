/**
 * Универсальная функция логирования JS ошибок
 * Подключать ПЕРВЫМ перед всеми скриптами
 */

window.logJSError = function(message, context = {}) {
    // Получаем CSRF токен
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    // Отправляем на сервер
    fetch('/api/log-js-error/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            message: message,
            source: context.file || window.location.pathname,
            lineno: context.lineno || 0,
            url: window.location.href,
            userAgent: navigator.userAgent,
            context: context
        })
    }).catch(err => console.error('Failed to log error:', err));
    
    // Дублируем в консоль для разработки
    console.error('[LOGGED]', message, context);
};

// Глобальный обработчик всех JS ошибок
window.addEventListener('error', function(event) {
    window.logJSError(event.message, {
        file: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error ? event.error.stack : null
    });
});

// Обработчик необработанных Promise
window.addEventListener('unhandledrejection', function(event) {
    window.logJSError('Unhandled Promise Rejection: ' + event.reason, {
        file: 'promise',
        reason: event.reason
    });
});