// Помощник для редактирования характеристик
(function() {
    'use strict';
    
    django.jQuery(document).ready(function($) {
        // Добавляем кнопку "Проверить JSON" рядом с полями specs
        $('textarea[name^="specs"]').each(function() {
            const textarea = $(this);
            const validateBtn = $('<button type="button" class="button" style="margin-left: 10px;">✓ Проверить JSON</button>');
            
            validateBtn.on('click', function() {
                try {
                    const json = JSON.parse(textarea.val());
                    alert('✅ JSON корректен!\n\nКлючей: ' + Object.keys(json).length);
                } catch (e) {
                    alert('❌ Ошибка в JSON:\n\n' + e.message);
                }
            });
            
            textarea.after(validateBtn);
        });
    });
})();