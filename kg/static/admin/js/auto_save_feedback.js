document.addEventListener('DOMContentLoaded', function() {
    // Находим все селекты для приоритета, статуса и менеджера
    const selects = document.querySelectorAll('select[name="priority"], select[name="status"], select[name="manager"]');
    
    selects.forEach(select => {
        const originalValue = select.value;
        
        select.addEventListener('change', function() {
            // Автоматически отправляем форму при изменении
            const form = this.closest('form');
            if (form) {
                // Ищем кнопку "Сохранить"
                const saveButton = form.querySelector('input[name="_save"]');
                if (saveButton) {
                    saveButton.click();
                }
            }
        });
    });
});