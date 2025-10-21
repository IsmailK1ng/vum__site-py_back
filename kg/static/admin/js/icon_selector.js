(function($) {
    'use strict';
    
    if (typeof $ === 'undefined') {
        console.error('jQuery не найден!');
        return;
    }
    
    $(document).ready(function() {        
        // ============================================
        // АВТОПЕРЕВОД ХАРАКТЕРИСТИК
        // ============================================
        const TRANSLATIONS = {
            'Дизель': { ky: 'Дизель', en: 'Diesel' },
            'Бензин': { ky: 'Бензин', en: 'Gasoline' },
            'ГАЗ + Бензин': { ky: 'Газ + Бензин', en: 'GAS + Gasoline' },
            'Климат-контроль': { ky: 'Климат-контроль', en: 'Climate control' },
            'цистерна, форма круглая': { ky: 'цистерна, формасы тегерек', en: 'tank, round shape' },
            'кг': { ky: 'кг', en: 'kg' },
            'л.с.': { ky: 'а.к.', en: 'hp' },
            'м²': { ky: 'м²', en: 'm²' },
            'м³': { ky: 'м³', en: 'm³' },
            'м2': { ky: 'м2', en: 'm2' },
            'м3': { ky: 'м3', en: 'm3' }
        };

        // Автозаполнение при вводе RU
        $(document).on('blur', 'input[name*="value_ru"]', function() {
            const $row = $(this).closest('tr');
            const ruValue = $(this).val().trim();
            
            if (!ruValue) return;
            
            const $kyInput = $row.find('input[name*="value_ky"]');
            const $enInput = $row.find('input[name*="value_en"]');
            
            if (!$kyInput.val() || !$enInput.val()) {
                let kyValue = ruValue;
                let enValue = ruValue;
                
                Object.keys(TRANSLATIONS).forEach(ruTerm => {
                    if (ruValue.includes(ruTerm)) {
                        const translated = TRANSLATIONS[ruTerm];
                        kyValue = kyValue.replace(ruTerm, translated.ky);
                        enValue = enValue.replace(ruTerm, translated.en);
                    }
                });
                
                if (!$kyInput.val()) $kyInput.val(kyValue);
                if (!$enInput.val()) $enInput.val(enValue);
            }
        });

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