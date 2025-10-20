(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Находим все редактируемые селекты в списке
        const editableSelects = $('#result_list select[name^="priority"], #result_list select[name^="status"], #result_list select[name^="manager"]');
        
        editableSelects.each(function() {
            const select = $(this);
            const originalValue = select.val();
            
            select.on('change', function() {
                const newValue = $(this).val();
                const row = $(this).closest('tr');
                const objectId = row.find('input[name="_selected_action"]').val();
                
                if (!objectId) {
                    console.error('ID заявки не найден');
                    return;
                }
                
                // Определяем какое поле изменилось
                let fieldName = '';
                if ($(this).attr('name').includes('priority')) {
                    fieldName = 'priority';
                } else if ($(this).attr('name').includes('status')) {
                    fieldName = 'status';
                } else if ($(this).attr('name').includes('manager')) {
                    fieldName = 'manager';
                }
                
                // Показываем индикатор загрузки
                $(this).css('opacity', '0.5');
                
                // Отправляем AJAX запрос
                $.ajax({
                    url: `/admin/main/kgfeedback/${objectId}/change/`,
                    method: 'POST',
                    data: {
                        [fieldName]: newValue,
                        '_save': 'Сохранить',
                        'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
                    },
                    success: function() {
                        // Анимация успешного сохранения
                        select.css({
                            'opacity': '1',
                            'background': '#d4edda',
                            'transition': 'all 0.3s'
                        });
                        
                        setTimeout(() => {
                            select.css('background', '');
                        }, 1000);
                    },
                    error: function(xhr) {
                        // Возвращаем старое значение при ошибке
                        select.val(originalValue);
                        select.css('opacity', '1');
                        alert('Ошибка сохранения. Попробуйте еще раз.');
                    }
                });
            });
        });
    });
})(django.jQuery);