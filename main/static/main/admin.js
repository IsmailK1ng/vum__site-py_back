(function() {
    if (typeof django === 'undefined' || typeof django.jQuery === 'undefined') {
        setTimeout(arguments.callee, 50);
        return;
    }
    
    console.log('✅ Admin JS загружен');
    
    django.jQuery(document).ready(function() {
        var $ = django.jQuery;
        
        // Функция обновления видимости полей
        function updateFieldsForRow(row, selectedType) {
            console.log('Обновляем поля для типа:', selectedType);
            console.log('Строка найдена:', row.length > 0 ? 'ДА' : 'НЕТ', row.attr('id'));
            
            var textTd = row.find('td.field-text');
            var imageTd = row.find('td.field-image');
            var youtubeTd = row.find('td.field-youtube_url');
            var videoTd = row.find('td.field-video_file');
            
            // Альтернативный поиск если классы не сработали
            if (!textTd.length) {
                // console.log('⚠️ TD с классами не найдены, ищем по содержимому');
                row.find('td').each(function() {
                    var td = $(this);
                    if (td.find('textarea[id*="-text"]').length) textTd = td;
                    if (td.find('input[type="file"][id*="-image"]').length) imageTd = td;
                    if (td.find('input[id*="-youtube_url"]').length) youtubeTd = td;
                    if (td.find('input[type="file"][id*="-video_file"]').length) videoTd = td;
                });
            }
            
            console.log('Найденные TD элементы:', {
                text: textTd.length,
                image: imageTd.length,
                youtube: youtubeTd.length,
                video: videoTd.length
            });
            
            // Если ничего не нашли, выводим структуру строки
            if (!textTd.length && !imageTd.length) {
                // console.log('⚠️ TD элементы не найдены! Структура строки:');
                row.find('td').each(function(i) {
                    console.log(`  TD[${i}]: class="${$(this).attr('class')}" содержит:`, 
                               $(this).find('input, textarea, select').attr('id') || 'другое');
                });
            }
            
            // Показываем все
            textTd.css('display', '');
            imageTd.css('display', '');
            youtubeTd.css('display', '');
            videoTd.css('display', '');
            
            // Скрываем ненужные
            switch(selectedType) {
                case 'text':
                case 'Текст':
                    // console.log('🔴 Скрываем: image, youtube, video');
                    imageTd.css('display', 'none');
                    youtubeTd.css('display', 'none');
                    videoTd.css('display', 'none');
                    // Проверяем что действительно скрыто
                    console.log('Проверка скрытия:', {
                        image: imageTd.is(':hidden'),
                        youtube: youtubeTd.is(':hidden'),
                        video: videoTd.is(':hidden')
                    });
                    break;
                case 'image':
                case 'Изображение':
                    // console.log('🔴 Скрываем: text, youtube, video');
                    textTd.css('display', 'none');
                    youtubeTd.css('display', 'none');
                    videoTd.css('display', 'none');
                    console.log('Проверка скрытия:', {
                        text: textTd.is(':hidden'),
                        youtube: youtubeTd.is(':hidden'),
                        video: videoTd.is(':hidden')
                    });
                    break;
                case 'youtube':
                case 'YouTube видео':
                    // console.log('🔴 Скрываем: text, image, video');
                    textTd.css('display', 'none');
                    imageTd.css('display', 'none');
                    videoTd.css('display', 'none');
                    break;
                case 'video':
                case 'Видео файл':
                    // console.log('🔴 Скрываем: text, image, youtube');
                    textTd.css('display', 'none');
                    imageTd.css('display', 'none');
                    youtubeTd.css('display', 'none');
                    break;
                default:
                    // console.log('⚠️ Неизвестный тип:', selectedType);
            }
        }
        
        // Маппинг текста на значения
        function textToValue(text) {
            var mapping = {
                'Текст': 'text',
                'Изображение': 'image',
                'YouTube видео': 'youtube',
                'Видео файл': 'video',
                '---------': '',
                '': ''
            };
            // console.log('Маппинг:', text, '->', mapping[text] || text);
            return mapping[text] || text;
        }
        
        // Инициализация существующих строк
        function initExistingRows() {
            $('select[id*="block_type"]').each(function() {
                var select = $(this);
                var row = select.closest('tr');
                if (!row.hasClass('empty-form')) {
                    updateFieldsForRow(row, select.val());
                }
            });
        }
        
        // Запускаем инициализацию
        initExistingRows();
        
        // ГЛАВНОЕ РЕШЕНИЕ - MutationObserver для Select2 текста
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                // Следим за изменением текста в Select2
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    var target = $(mutation.target);
                    
                    // Проверяем, это ли Select2 selection текст
                    if (target.hasClass('select2-selection__rendered') || 
                        target.closest('.select2-selection__rendered').length) {
                        
                        var rendered = target.hasClass('select2-selection__rendered') ? 
                                     target : target.closest('.select2-selection__rendered');
                        
                        var containerId = rendered.attr('id');
                        if (containerId && containerId.includes('blocks')) {
                            var selectedText = rendered.text().trim();
                            var selectedValue = textToValue(selectedText);
                            
                            // console.log('📝 Select2 текст изменился:', selectedText, '->', selectedValue);
                            
                            // Находим строку - пробуем разные способы
                            var selectId = containerId.replace('-container', '');
                            var select = $('#' + selectId);
                            // console.log('Select найден:', select.length > 0, selectId);
                            
                            var row = select.closest('tr');
                            // console.log('Row через select.closest:', row.length > 0);
                            
                            // Альтернативный способ найти row
                            if (!row.length) {
                                row = rendered.closest('tr');
                                // console.log('Row через rendered.closest:', row.length > 0);
                            }
                            
                            if (row.length) {
                                updateFieldsForRow(row, selectedValue);
                                
                                // Обновляем значение в оригинальном select
                                if (select.val() !== selectedValue) {
                                    select.val(selectedValue);
                                }
                            } else {
                                // console.log('❌ Строка не найдена!');
                            }
                        }
                    }
                }
                
                // Обработка новых строк
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeName === 'TR' && !$(node).hasClass('empty-form')) {
                            // console.log('🆕 Новая строка добавлена');
                            setTimeout(function() {
                                var select = $(node).find('select[id*="block_type"]');
                                if (select.length) {
                                    updateFieldsForRow($(node), select.val());
                                }
                            }, 500);
                        }
                    });
                }
            });
        });
        
        // Наблюдаем за всем документом
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true,
            characterDataOldValue: true
        });
        
        // console.log('👀 MutationObserver запущен');
        
        // Дополнительный обработчик через интервал для проверки текста
        setInterval(function() {
            $('.select2-selection__rendered').each(function() {
                var rendered = $(this);
                var containerId = rendered.attr('id');
                
                if (containerId && containerId.includes('blocks')) {
                    var currentText = rendered.text().trim();
                    var lastText = rendered.data('last-text');
                    
                    if (currentText !== lastText) {
                        rendered.data('last-text', currentText);
                        var selectedValue = textToValue(currentText);
                        
                        // console.log('🔄 Текст изменился:', currentText, '->', selectedValue);
                        
                        var selectId = containerId.replace('-container', '');
                        var select = $('#' + selectId);
                        var row = select.closest('tr');
                        
                        if (row.length) {
                            updateFieldsForRow(row, selectedValue);
                        }
                    }
                }
            });
        }, 300);
        
        // Стандартные обработчики на всякий случай
        $(document).on('change select2:select', 'select[id*="block_type"]', function() {
            // console.log('📌 Стандартное событие');
            var row = $(this).closest('tr');
            updateFieldsForRow(row, $(this).val());
        });
        
        // console.log('✅ Скрипт полностью инициализирован');
    });
})();