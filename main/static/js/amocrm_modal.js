document.addEventListener('DOMContentLoaded', function() {
    // Создаём модальное окно
    const modal = document.createElement('div');
    modal.className = 'amocrm-modal';
    modal.innerHTML = `
        <div class="amocrm-modal-content">
            <div class="amocrm-modal-header">
                <h2>Ошибка отправки в amoCRM</h2>
                <button class="amocrm-modal-close">&times;</button>
            </div>
            <div class="amocrm-modal-body">
                <div class="amocrm-error-text"></div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Обработчик для бейджей с ошибками
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('amocrm-error-badge')) {
            const errorText = e.target.getAttribute('data-error');
            modal.querySelector('.amocrm-error-text').textContent = errorText;
            modal.style.display = 'block';
        }
    });
    
    // Закрытие модального окна
    modal.querySelector('.amocrm-modal-close').addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Закрытие при клике вне окна
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Закрытие по ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    });
});