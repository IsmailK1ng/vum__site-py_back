/*** Динамическая фильтрация параметров по категории + подсказки ***/

(function(){
    'use strict';
    
    var suggestionsCache = {};
    
    window.addEventListener('load', function(){
        setTimeout(initParameterFilter, 300);
    });
    
    function initParameterFilter() {
        var $ = window.jQuery;
        if (!$) return;
        
        var $sel = $('select[name*="parameters"][name$="-category"]');
        if ($sel.length === 0) return;
        
        if ($('#pf-filter-box').length) return;
        
        var $table = $sel.first().closest('table');
        if (!$table.length) return;
        
        // Собираем категории
        var cats = {};
        $sel.first().find('option').each(function(){
            var val = this.value;
            var text = this.textContent.trim();
            if (val && text && text !== '---------') {
                cats[val] = text;
            }
        });
        
        if (Object.keys(cats).length === 0) return;
        
        // Создаём UI фильтра
        var $box = $('<div>', {
            id: 'pf-filter-box',
            css: {
                background: 'linear-gradient(145deg, #215cf7 0%, #000000ff 140%)',
                padding: '12px 20px',
                borderRadius: '8px',
                margin: '10px 0',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                flexWrap: 'wrap',
                boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)'
            }
        });
        
        var $label = $('<span>', {
            html: 'Фильтр:',
            css: { color: '#fff', fontWeight: '600', fontSize: '16px' }
        });
        
        var $filterSel = $('<select>', {
            id: 'pf-select',
            css: {
                padding: '8px 12px',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                minWidth: '200px',
                cursor: 'pointer'
            }
        });
        $filterSel.append('<option value="">— Все категории —</option>');
        
        $.each(cats, function(val, text) {
            $filterSel.append($('<option>', { value: val, text: text }));
        });
        
        var $count = $('<span>', {
            id: 'pf-count',
            css: {
                color: '#fff',
                fontSize: '12px',
                background: 'rgba(255,255,255,0.2)',
                padding: '4px 12px',
                borderRadius: '12px'
            }
        });
        
        var $addBtn = $('<button>', {
            type: 'button',
            id: 'pf-add-btn',
            text: '+ Добавить',
            css: {
                background: '#10b981',
                color: '#fff',
                border: 'none',
                padding: '8px 14px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                marginLeft: 'auto'
            }
        });
        
        $box.append($label, $filterSel, $count, $addBtn);
        $table.before($box);
        
        // Функция фильтрации
        function doFilter(cat) {
            var shown = 0, total = 0;
            var $allSel = $('select[name*="parameters"][name$="-category"]');
            
            $allSel.each(function() {
                var $row = $(this).closest('tr');
                var rowId = $row.attr('id') || '';
                
                if (rowId.indexOf('__prefix__') > -1 || rowId.indexOf('-empty') > -1) return;
                if ($row.find('input[name$="-DELETE"]:checked').length) return;
                
                total++;
                
                if (!cat || $(this).val() === cat) {
                    $row.show();
                    shown++;
                } else {
                    $row.hide();
                }
            });
            
            $count.text(cat ? 'Показано: ' + shown + ' из ' + total : 'Всего: ' + total);
        }
        
        $filterSel.on('change', function() {
            doFilter(this.value);
        });
        
        // Кнопка добавления
        $addBtn.on('click', function() {
            var selectedCat = $filterSel.val();
            var addLink = $table.find('a.addlink')[0];
            
            if (addLink) {
                addLink.click();
                
                setTimeout(function() {
                    var $newSelect = $('select[name*="parameters"][name$="-category"]').filter(function(){
                        return this.name.indexOf('__prefix__') === -1;
                    }).last();
                    
                    var $newRow = $newSelect.closest('tr');
                    
                    if (selectedCat) {
                        $newSelect.val(selectedCat);
                        // Загружаем подсказки для новой строки
                        loadSuggestions($newSelect, selectedCat);
                    }
                    
                    $newRow.show();
                    $newRow.css('background', 'rgba(102, 126, 234, 0.15)');
                    setTimeout(function() {
                        $newRow.css('background', '');
                    }, 2000);
                    
                    updateCountWithNewRow($newRow, $filterSel.val());
                    
                }, 500);
            }
        });
        
        function updateCountWithNewRow($newRow, currentCat) {
            var shown = 0, total = 0;
            
            $('select[name*="parameters"][name$="-category"]').each(function() {
                var $row = $(this).closest('tr');
                var rowId = $row.attr('id') || '';
                
                if (rowId.indexOf('__prefix__') > -1 || rowId.indexOf('-empty') > -1) return;
                if ($row.find('input[name$="-DELETE"]:checked').length) return;
                
                total++;
                
                if ($row.is($newRow)) {
                    shown++;
                    return;
                }
                
                if (!currentCat || $(this).val() === currentCat) {
                    $row.show();
                    shown++;
                } else {
                    $row.hide();
                }
            });
            
            $count.text(currentCat ? 'Показано: ' + shown + ' из ' + total : 'Всего: ' + total);
        }
        
        $addBtn.on('mouseenter', function() {
            $(this).css('background', '#059669');
        }).on('mouseleave', function() {
            $(this).css('background', '#10b981');
        });
        
        // ========== ПОДСКАЗКИ ==========
        
        function loadSuggestions($categorySelect, category) {
            if (!category) return;
            
            var $row = $categorySelect.closest('tr');
            var $textInput = $row.find('input[name*="-text"]').first();
            
            if (!$textInput.length) return;
            
            // Проверяем кеш
            if (suggestionsCache[category]) {
                showSuggestions($textInput, suggestionsCache[category]);
                return;
            }
            
            // Загружаем с сервера
            $.ajax({
                url: '/admin/main/product/api/parameter-suggestions/',
                data: { category: category },
                success: function(data) {
                    if (data.suggestions && data.suggestions.length > 0) {
                        suggestionsCache[category] = data.suggestions;
                        showSuggestions($textInput, data.suggestions);
                    }
                }
            });
        }
        
        function showSuggestions($input, suggestions) {
            // Удаляем старые подсказки
            $input.closest('td').find('.pf-suggestions').remove();
            
            if (!suggestions || suggestions.length === 0) return;
            
            var $container = $('<div>', {
                'class': 'pf-suggestions',
                css: {
                    position: 'absolute',
                    zIndex: 1000,
                    background: '#fff',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    minWidth: '250px',
                    marginTop: '2px'
                }
            });
            
            var $header = $('<div>', {
                html: '📋 Ранее использовались:',
                css: {
                    padding: '8px 12px',
                    background: '#f8f9fa',
                    borderBottom: '1px solid #eee',
                    fontSize: '12px',
                    color: '#666',
                    fontWeight: '600'
                }
            });
            $container.append($header);
            
            suggestions.forEach(function(item) {
                var $item = $('<div>', {
                    text: item.text,
                    css: {
                        padding: '8px 12px',
                        cursor: 'pointer',
                        borderBottom: '1px solid #f0f0f0',
                        fontSize: '13px',
                        transition: 'background 0.2s'
                    }
                });
                
                // Счётчик использований
                var $badge = $('<span>', {
                    text: item.count + 'x',
                    css: {
                        float: 'right',
                        background: '#e3f2fd',
                        color: '#1976d2',
                        padding: '2px 6px',
                        borderRadius: '10px',
                        fontSize: '11px'
                    }
                });
                $item.append($badge);
                
                $item.on('mouseenter', function() {
                    $(this).css('background', '#f0f7ff');
                }).on('mouseleave', function() {
                    $(this).css('background', '#fff');
                });
                
                $item.on('click', function() {
                    $input.val(item.text);
                    $container.remove();
                    $input.focus();
                });
                
                $container.append($item);
            });
            
            // Кнопка закрытия
            var $close = $('<div>', {
                html: '✕ Закрыть',
                css: {
                    padding: '6px 12px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    color: '#999',
                    fontSize: '12px',
                    background: '#f8f9fa'
                }
            });
            $close.on('click', function() {
                $container.remove();
            });
            $container.append($close);
            
            // Позиционируем относительно input
            var $td = $input.closest('td');
            $td.css('position', 'relative');
            $td.append($container);
            
            // Закрытие по клику вне
            setTimeout(function() {
                $(document).one('click', function(e) {
                    if (!$(e.target).closest('.pf-suggestions').length) {
                        $container.remove();
                    }
                });
            }, 100);
        }
        
        // Обработчик изменения категории в строках
        $(document).on('change', 'select[name*="parameters"][name$="-category"]', function() {
            var category = $(this).val();
            if (category) {
                loadSuggestions($(this), category);
            }
        });
        
        // Показ подсказок при фокусе на поле ввода
        $(document).on('focus', 'input[name*="parameters"][name*="-text"]', function() {
            var $input = $(this);
            var $row = $input.closest('tr');
            var $catSelect = $row.find('select[name$="-category"]');
            var category = $catSelect.val();
            
            if (category && !$input.val()) {
                loadSuggestions($catSelect, category);
            }
        });
        
        doFilter('');
    }
    
})();