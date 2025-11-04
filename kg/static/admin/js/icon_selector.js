(function($) {
    'use strict';
    
    if (typeof $ === 'undefined') {
        return;
    }
    
    $(document).ready(function() {        
        initIconSelectors();
        
        $(document).on('click', '.add-row a', function() {
            setTimeout(function() {
                initIconSelectors();
            }, 500);
        });
        
        function initIconSelectors() {
            $(document).off('click', '.icon-card').on('click', '.icon-card', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const $card = $(this);
                const templateId = $card.data('template-id');
                const iconUrl = $card.data('icon-url');
                
                const $row = $card.closest('tr.form-row');
                if (!$row.length) {
                    return;
                }
                
                const $table = $row.closest('table');
                const $allRows = $table.find('tbody tr.form-row');
                const rowIndex = $allRows.index($row);
        
                const fieldName = 'card_specs-' + rowIndex + '-selected_template';
                let $hiddenInput = $row.find('input[name="' + fieldName + '"]');
                
                if ($hiddenInput.length === 0) {
                    $hiddenInput = $('<input>', {
                        type: 'hidden',
                        name: fieldName,
                        id: 'id_' + fieldName,
                        class: 'selected-template-field'
                    });
                    
                    $row.find('td').last().append($hiddenInput);
                } 
                
                $hiddenInput.val(templateId);

                const $iconField = $row.find('input[name*="-icon"]');
                if ($iconField.length) {
                    $iconField.val(iconUrl);
                }
                
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