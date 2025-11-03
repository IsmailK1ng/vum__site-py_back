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
            console.log('🔄 Применяем toggleFieldsByBlockType');
            
            $('.inline-related').each(function() {
                var $inline = $(this);
                var $blockTypeSelect = $inline.find('select[id$="-block_type"]');
                
                if ($blockTypeSelect.length === 0) return;
                
                var blockType = $blockTypeSelect.val();
                console.log('Тип блока:', blockType);
                
                // Находим поля (для всех языков)
                var $titleFields = $inline.find('.field-title_uz, .field-title_ru, .field-title_en');
                var $textFields = $inline.find('.field-text_uz, .field-text_ru, .field-text_en');
                var $imageField = $inline.find('.field-image');
                var $youtubeField = $inline.find('.field-youtube_url');
                var $videoField = $inline.find('.field-video_file');
                
                // Скрываем все поля контента
                $titleFields.hide();
                $textFields.hide();
                $imageField.hide();
                $youtubeField.hide();
                $videoField.hide();
                
                // Показываем нужные в зависимости от типа
                if (blockType === 'text') {
                    $titleFields.show();
                    $textFields.show();
                    console.log('  → Показываем: title, text');
                } else if (blockType === 'image') {
                    $titleFields.show();
                    $imageField.show();
                    console.log('  → Показываем: title, image');
                } else if (blockType === 'youtube') {
                    $titleFields.show();
                    $youtubeField.show();
                    console.log('  → Показываем: title, youtube');
                } else if (blockType === 'video') {
                    $titleFields.show();
                    $videoField.show();
                    console.log('  → Показываем: title, video');
                } else {
                    console.log('  → Тип не выбран, скрываем всё');
                }
            });
        }
        
        $(document).ready(function() {
            setTimeout(toggleFieldsByBlockType, 300);
        });
        
        $(document).on('change', 'select[id$="-block_type"]', function() {
            toggleFieldsByBlockType();
        });
        
        $(document).on('formset:added', function() {
            setTimeout(toggleFieldsByBlockType, 200);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBlockTypeToggle);
    } else {
        initBlockTypeToggle();
    }
})();