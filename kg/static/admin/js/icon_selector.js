(function($) {
    'use strict';
    
    if (typeof $ === 'undefined') {
        console.error('❌ jQuery не загружен! Проверьте подключение.');
        return;
    }
    
    $(document).ready(function() {
        console.log('🚀 Icon Selector загружен (jQuery работает)');
        
        // ============================================
        // АВТОПЕРЕВОД ХАРАКТЕРИСТИК
        // ============================================
        const translations = {
            'Дизель': { ky: 'Дизель', en: 'Diesel' },
            'Бензин': { ky: 'Бензин', en: 'Gasoline' },
            'кг': { ky: 'кг', en: 'kg' },
            'л.с.': { ky: 'а.к.', en: 'hp' },
            'м³': { ky: 'м³', en: 'm³' },
            'м²': { ky: 'м²', en: 'm²' },
            'Климат-контроль': { ky: 'Климат-контроль', en: 'Climate control' },
            '4x2': { ky: '4x2', en: '4x2' },
            '4×2': { ky: '4×2', en: '4×2' },
            '4х2': { ky: '4х2', en: '4х2' }
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
                
                Object.keys(translations).forEach(ruTerm => {
                    if (ruValue.includes(ruTerm)) {
                        const translated = translations[ruTerm];
                        kyValue = kyValue.replace(ruTerm, translated.ky);
                        enValue = enValue.replace(ruTerm, translated.en);
                    }
                });
                
                if (!$kyInput.val()) $kyInput.val(kyValue);
                if (!$enInput.val()) $enInput.val(enValue);
                
                console.log('✅ Автоперевод:', ruValue, '→', kyValue, '/', enValue);
            }
        });

        // ============================================
        // ВЫБОР ИКОНОК
        // ============================================
        
        initIconSelectors();
        
        // Следим за добавлением новых строк
        $(document).on('click', '.add-row a', function() {
            setTimeout(function() {
                console.log('➕ Добавлена новая строка');
                initIconSelectors();
            }, 500);
        });
        
        function initIconSelectors() {
            console.log('🔧 Инициализация селекторов иконок...');
            
            // Используем делегирование событий через document
            $(document).off('click', '.icon-card').on('click', '.icon-card', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const $card = $(this);
                const templateId = $card.data('template-id');
                const iconUrl = $card.data('icon-url');
                const iconName = $card.find('small').text();
                
                console.log('🖱️ Клик по иконке:', iconName, 'ID:', templateId);
                
                const $row = $card.closest('tr.form-row');
                if (!$row.length) {
                    console.error('❌ Строка не найдена');
                    return;
                }
                
                // Получаем индекс строки
                const $table = $row.closest('table');
                const $allRows = $table.find('tbody tr.form-row');
                const rowIndex = $allRows.index($row);
                
                console.log('📍 Индекс строки:', rowIndex);
                
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
                    console.log('✅ Создано поле:', fieldName);
                } else {
                    console.log('🔄 Поле уже существует:', fieldName);
                }
                
                // Устанавливаем значение
                $hiddenInput.val(templateId);
                console.log('💾 Значение установлено:', fieldName, '=', templateId);
                
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
                    console.log('🖼️ Превью обновлено');
                }
                
                console.log('✅ Иконка выбрана успешно');
            });
            
            console.log('✅ Селекторы инициализированы');
        }
        
        console.log('✅ Icon Selector готов к работе');
    });
    
})(django.jQuery || jQuery || window.jQuery || $);

