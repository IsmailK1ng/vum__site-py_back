(function($) {
    'use strict';
    
    if (typeof $ === 'undefined') {
        console.error('jQuery не найден!');
        return;
    }
    
    $(document).ready(function() {        
   
        // ============================================
        // ВЫБОР ИКОНОК
        // ============================================
        
        initIconSelectors();
        
        // Следим за добавлением новых строк
        $(document).on('click', '.add-row a', function() {
            setTimeout(function() {
                initIconSelectors();
            }, 500);
        });
        
        function initIconSelectors() {
            // Используем делегирование событий через document
            $(document).off('click', '.icon-card').on('click', '.icon-card', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const $card = $(this);
                const templateId = $card.data('template-id');
                const iconUrl = $card.data('icon-url');
                
                const $row = $card.closest('tr.form-row');
                if (!$row.length) {
                    console.warn('Строка не найдена');
                    return;
                }
                
                // Получаем индекс строки
                const $table = $row.closest('table');
                const $allRows = $table.find('tbody tr.form-row');
                const rowIndex = $allRows.index($row);
        
                // Создаём или обновляем скрытое поле
                const fieldName = 'card_specs-' + rowIndex + '-selected_template';
                let $hiddenInput = $row.find('input[name="' + fieldName + '"]');
                
                if ($hiddenInput.length === 0) {
                    // Создаём новое поле
                    $hiddenInput = $('<input>', {
                        type: 'hidden',
                        name: fieldName,
                        id: 'id_' + fieldName,
                        class: 'selected-template-field'
                    });
                    
                    // Добавляем в конец строки
                    $row.find('td').last().append($hiddenInput);
                } 
                
                // Устанавливаем значение
                $hiddenInput.val(templateId);

                // КРИТИЧНО: Обновляем поле icon (для сохранения в базу)
                const $iconField = $row.find('input[name*="-icon"]');
                if ($iconField.length) {
                    $iconField.val(iconUrl);
                }
                
                // Визуальная обратная связь
                $row.find('.icon-card').css({
                    'border': '2px solid #ddd',
                    'background': '#fff',
                    'transform': 'scale(1)'
                });
                
                $card.css({
                    'border': '3px solid #2e7d32',
                    'background': '#e8f5e9',
                    'transform': 'scale(1.05)'
                });
                
                // Обновляем превью
                const $preview = $row.find('td.field-icon_preview img');
                if ($preview.length) {
                    $preview.attr('src', iconUrl).css({
                        'border': '2px solid #2e7d32',
                        'border-radius': '8px'
                    });
                }
            });
        }
    });
})(django.jQuery || jQuery || window.jQuery || $);