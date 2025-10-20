(function($) {
    'use strict';

    if (typeof $ === 'undefined' || typeof $.ajax === 'undefined') {
        return;
    }

    $(document).ready(function() {
        const editableSelects = $('select').filter(function() {
            const name = $(this).attr('name') || '';
            return name.match(/priority|status|manager/);
        });

        if (editableSelects.length === 0) {
            return;
        }

        editableSelects.each(function() {
            const select = $(this);
            const row = select.closest('tr');
            const checkbox = row.find('input[name="_selected_action"]');
            const objectId = checkbox.val();

            if (!objectId) {
                return;
            }

            select.data('original-value', select.val());

            select.on('change', function() {
                const newValue = $(this).val();
                const originalValue = select.data('original-value');
                
                let fieldName = '';
                
                if (select.attr('name').includes('priority')) fieldName = 'priority';
                else if (select.attr('name').includes('status')) fieldName = 'status';
                else if (select.attr('name').includes('manager')) fieldName = 'manager';

                if (!fieldName) {
                    return;
                }

                const saveUrl = `/api/kg/feedback-update/${objectId}/quick-update/`;

                select.css({
                    'opacity': '0.5',
                    'pointer-events': 'none'
                });

                $.ajax({
                    url: saveUrl,
                    method: 'PATCH',
                    contentType: 'application/json',
                    headers: {
                        'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
                    },
                    data: JSON.stringify({
                        [fieldName]: newValue || ''
                    }),
                    success: function(response) {
                        select.data('original-value', newValue);
                        
                        select.css({
                            'opacity': '1',
                            'pointer-events': 'auto',
                            'background': 'linear-gradient(90deg, #d4edda 0%, #c3e6cb 100%)',
                            'transition': 'all 0.3s',
                            'border': '2px solid #28a745'
                        });
                        
                        setTimeout(() => {
                            select.css({
                                'background': '',
                                'border': ''
                            });
                        }, 2000);
                    },
                    error: function(xhr) {
                        select.val(originalValue);
                        
                        select.css({
                            'opacity': '1',
                            'pointer-events': 'auto',
                            'background': '#f8d7da',
                            'border': '2px solid #dc3545'
                        });
                        
                        setTimeout(() => {
                            select.css({
                                'background': '',
                                'border': ''
                            });
                        }, 2000);
                        
                        alert('Ошибка сохранения. Попробуйте обновить страницу.');
                    }
                });
            });
        });
    });
})(jQuery);