(function() {
    'use strict';

    console.log('✅ news_block_dynamic.js загружен');

    function initBlockTypeToggle() {
        if (typeof django === 'undefined' || typeof django.jQuery === 'undefined') {
            setTimeout(initBlockTypeToggle, 100);
            return;
        }

        var $ = django.jQuery;
        console.log('✅ jQuery готов');

        function toggleFieldsByBlockType() {
            console.log('🔄 Скрываем/показываем поля');
            
            $('.inline-related:not(.empty-form)').each(function(idx) {
                var $block = $(this);
                var $typeSelect = $block.find('select[name$="-block_type"]');
                
                if ($typeSelect.length === 0) return;
                
                var blockType = $typeSelect.val();
                console.log('Блок', idx, '→', blockType || '(не выбран)');
                
                // Находим .ui-tabs контейнеры
                var $titleTabs = $block.find('.ui-tabs').filter(function() {
                    return $(this).find('[id*="title"]').length > 0;
                });
                
                var $textTabs = $block.find('.ui-tabs').filter(function() {
                    return $(this).find('[id*="text"]').length > 0 && 
                           $(this).find('[id*="title"]').length === 0;
                });
                
                // Находим обычные поля (без вкладок)
                var $imageField = $block.find('.form-group').filter(function() {
                    return $(this).attr('class').includes('field-image');
                });
                
                var $youtubeField = $block.find('.form-group').filter(function() {
                    return $(this).attr('class').includes('field-youtube');
                });
                
                var $videoField = $block.find('.form-group').filter(function() {
                    return $(this).attr('class').includes('field-video');
                });
                
                console.log('  Найдено:', {
                    title: $titleTabs.length,
                    text: $textTabs.length,
                    image: $imageField.length,
                    youtube: $youtubeField.length,
                    video: $videoField.length
                });
                
                // СКРЫВАЕМ ВСЁ
                $titleTabs.hide();
                $textTabs.hide();
                $imageField.hide();
                $youtubeField.hide();
                $videoField.hide();
                
                // ПОКАЗЫВАЕМ нужное
                switch(blockType) {
                    case 'text':
                        $titleTabs.show();
                        $textTabs.show();
                        console.log('  ✅ Показали: заголовок + текст');
                        break;
                    case 'image':
                        $titleTabs.show();
                        $imageField.show();
                        console.log('  ✅ Показали: заголовок + фото');
                        break;
                    case 'youtube':
                        $titleTabs.show();
                        $youtubeField.show();
                        console.log('  ✅ Показали: заголовок + YouTube');
                        break;
                    case 'video':
                        $titleTabs.show();
                        $videoField.show();
                        console.log('  ✅ Показали: заголовок + видео');
                        break;
                    default:
                        console.log('  ℹ️ Тип не выбран — всё скрыто');
                }
            });
        }
        
        // ✅ ИСПРАВЛЕНИЕ 1: Запускаем НЕМЕДЛЕННО при загрузке и после каждого добавления
        $(document).ready(function() {
            toggleFieldsByBlockType();  // Без задержки!
            setTimeout(toggleFieldsByBlockType, 100);  // Дополнительно через 100ms
            setTimeout(toggleFieldsByBlockType, 500);  // И через 500ms для Django
        });
        
        // ✅ ИСПРАВЛЕНИЕ 2: Срабатывает сразу при изменении селекта
        $(document).on('change', 'select[name$="-block_type"]', function() {
            console.log('🔄 Селект изменён');
            toggleFieldsByBlockType();
        });
        
        // При добавлении нового блока
        $(document).on('formset:added', function() {
            toggleFieldsByBlockType();
            setTimeout(toggleFieldsByBlockType, 100);
            setTimeout(toggleFieldsByBlockType, 300);
        });
        
        
        var observer = new MutationObserver(function(mutations) {
            var shouldUpdate = false;
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length > 0) {
                    shouldUpdate = true;
                }
            });
            if (shouldUpdate) {
                setTimeout(toggleFieldsByBlockType, 100);
            }
        });
        
        // Следим за контейнером инлайнов
        var inlineContainer = document.querySelector('.inline-group');
        if (inlineContainer) {
            observer.observe(inlineContainer, {
                childList: true,
                subtree: true
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBlockTypeToggle);
    } else {
        initBlockTypeToggle();
    }
})();