(function() {
    'use strict';

    function initBlockTypeToggle() {
        if (typeof django === 'undefined' || typeof django.jQuery === 'undefined') {
            setTimeout(initBlockTypeToggle, 100);
            return;
        }

        var $ = django.jQuery;

        function toggleFieldsByBlockType() {
            $('.inline-related:not(.empty-form)').each(function(idx) {
                var $block = $(this);
                var $typeSelect = $block.find('select[name$="-block_type"]');

                if ($typeSelect.length === 0) return;

                var blockType = $typeSelect.val();

                var $titleTabs = $block.find('.ui-tabs').filter(function() {
                    return $(this).find('[id*="title"]').length > 0;
                });

                var $textTabs = $block.find('.ui-tabs').filter(function() {
                    return $(this).find('[id*="text"]').length > 0 &&
                           $(this).find('[id*="title"]').length === 0;
                });

                var $imageField = $block.find('.form-group').filter(function() {
                    return $(this).attr('class').includes('field-image');
                });

                var $youtubeField = $block.find('.form-group').filter(function() {
                    return $(this).attr('class').includes('field-youtube');
                });

                var $videoField = $block.find('.form-group').filter(function() {
                    return $(this).attr('class').includes('field-video');
                });

                $titleTabs.hide();
                $textTabs.hide();
                $imageField.hide();
                $youtubeField.hide();
                $videoField.hide();

                switch(blockType) {
                    case 'text':
                        $titleTabs.show();
                        $textTabs.show();
                        break;
                    case 'image':
                        $titleTabs.show();
                        $imageField.show();
                        break;
                    case 'youtube':
                        $titleTabs.show();
                        $youtubeField.show();
                        break;
                    case 'video':
                        $titleTabs.show();
                        $videoField.show();
                        break;
                }
            });
        }

        $(document).ready(function() {
            toggleFieldsByBlockType();
            setTimeout(toggleFieldsByBlockType, 100);
            setTimeout(toggleFieldsByBlockType, 500);
        });

        $(document).on('change', 'select[name$="-block_type"]', function() {
            toggleFieldsByBlockType();
        });

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
