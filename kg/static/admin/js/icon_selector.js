/**
 * Админка FAW - Помощники для работы с машинами
 * - Автоперевод характеристик
 * - Выбор иконок для характеристик
 * - Валидация JSON
 */

(function() {
    'use strict';
    
    django.jQuery(document).ready(function($) {
        console.log('🚀 FAW Admin Helper загружен');
        
        // ============================================
        // 1. АВТОПЕРЕВОД ХАРАКТЕРИСТИК
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
            '4х2': { ky: '4х2', en: '4х2' },
            '4x4': { ky: '4x4', en: '4x4' },
            'Механика': { ky: 'Механикалык', en: 'Manual' },
            'Автомат': { ky: 'Автоматтык', en: 'Automatic' }
        };

        // Автозаполнение при вводе RU
        $(document).on('blur', 'input[name*="value_ru"]', function() {
            const $row = $(this).closest('tr');
            const ruValue = $(this).val().trim();
            
            if (!ruValue) return;
            
            const $kyInput = $row.find('input[name*="value_ky"]');
            const $enInput = $row.find('input[name*="value_en"]');
            
            // Если поля пустые - заполняем автоматически
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
                
                if (!$kyInput.val()) {
                    $kyInput.val(kyValue);
                    console.log('✅ Автоперевод KY:', kyValue);
                }
                if (!$enInput.val()) {
                    $enInput.val(enValue);
                    console.log('✅ Автоперевод EN:', enValue);
                }
            }
        });

        // ============================================
        // 2. ВЫБОР ИКОНОК
        // ============================================
        
        // Инициализация при загрузке
        initIconSelectors();
        
        // Следим за добавлением новых строк
        $(document).on('click', '.add-row a', function() {
            setTimeout(function() {
                console.log('➕ Добавлена новая строка');
                initIconSelectors();
            }, 500);
        });
        
        function initIconSelectors() {
            // Используем делегирование событий для динамических элементов
            $(document).off('click', '.icon-card').on('click', '.icon-card', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const $card = $(this);
                const templateId = $card.data('template-id');
                const iconUrl = $card.data('icon-url');
                const iconName = $card.find('small').text();
                
                // Находим родительскую строку
                const $row = $card.closest('tr.form-row');
                if (!$row.length) {
                    console.error('❌ Не найдена строка формы');
                    return;
                }
                
                // Получаем индекс строки
                const $table = $row.closest('table');
                const $allRows = $table.find('tbody tr.form-row');
                const rowIndex = $allRows.index($row);
                
                console.log('🖱️ Клик по иконке:', iconName, 'строка:', rowIndex, 'ID:', templateId);
                
                // Находим или создаём скрытое поле
                const fieldName = 'card_specs-' + rowIndex + '-selected_template';
                let $hiddenInput = $row.find('input[name="' + fieldName + '"]');
                
                if ($hiddenInput.length === 0) {
                    // Создаём новое скрытое поле
                    $hiddenInput = $('<input>', {
                        type: 'hidden',
                        name: fieldName,
                        id: 'id_' + fieldName,
                        class: 'selected-template-field'
                    });
                    
                    // Добавляем в последнюю ячейку строки
                    $row.find('td').last().append($hiddenInput);
                    console.log('✅ Создано скрытое поле:', fieldName);
                } else {
                    console.log('🔄 Поле уже существует:', fieldName);
                }
                
                // Устанавливаем значение
                $hiddenInput.val(templateId);
                console.log('💾 Установлено:', fieldName, '=', templateId);
                
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
                const $preview = $row.find('td:nth-child(2) img');
                if ($preview.length) {
                    $preview.attr('src', iconUrl).css({
                        'border': '2px solid #2e7d32',
                        'border-radius': '8px'
                    });
                }
                
                // Показываем информацию
                const $info = $row.find('.selected-icon-info');
                if ($info.length) {
                    $info.find('.icon-name').text(iconName);
                    $info.show();
                }
                
                console.log('✅ Иконка выбрана успешно');
            });
        }

        // ============================================
        // 3. ВАЛИДАЦИЯ JSON
        // ============================================
        $('textarea[name^="specs"]').each(function() {
            const $textarea = $(this);
            const $validateBtn = $('<button>', {
                type: 'button',
                class: 'button',
                text: '✓ Проверить JSON',
                css: { 'margin-left': '10px' }
            });
            
            $validateBtn.on('click', function() {
                try {
                    const json = JSON.parse($textarea.val());
                    alert('✅ JSON корректен!\n\nКлючей: ' + Object.keys(json).length);
                } catch (e) {
                    alert('❌ Ошибка в JSON:\n\n' + e.message);
                }
            });
            
            $textarea.after($validateBtn);
        });
        
        console.log('✅ Все модули загружены');
    });
})();