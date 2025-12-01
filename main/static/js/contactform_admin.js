(function() {
    'use strict';

    function initContactFormAdmin() {
        if (typeof window.django === 'undefined' || typeof window.django.jQuery === 'undefined') {
            setTimeout(initContactFormAdmin, 100);
            return;
        }

        const $ = window.django.jQuery;
        const $form = $('#leads-filter-form');
        if ($form.length === 0) {
            setTimeout(initContactFormAdmin, 100);
            return;
        }

        // Применить фильтры
        $form.on('submit', function (e) {
            e.preventDefault();
            const params = new URLSearchParams();

            $form.find('input, select').each(function () {
                const $field = $(this);
                const name = $field.attr('name');
                const value = $field.val();

                if (name && value && value.trim() !== '') {
                    params.append(name, value.trim());
                }
            });

            const queryString = params.toString();
            window.location.href = window.location.pathname + (queryString ? '?' + queryString : '');
        });

        // Сброс
        $('#btn-reset').on('click', function (e) {
            e.preventDefault();
            window.location.href = window.location.pathname;
        });

        // Экспорт
        $('#btn-export').on('click', function (e) {
            e.preventDefault();

            const currentParams = new URLSearchParams(window.location.search);
            const selectedIds = [];
            $('input[name="_selected_action"]:checked').each(function () {
                selectedIds.push($(this).val());
            });

            if (selectedIds.length > 0) {
                selectedIds.forEach(id => currentParams.append('_selected_action', id));
            } else {
                currentParams.set('select_across', '1');
            }

            currentParams.set('action', 'export_to_excel');

            const $exportForm = $('<form>', {
                method: 'POST',
                action: window.location.pathname
            });

            const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
            if (csrfToken) {
                $exportForm.append($('<input>', {
                    type: 'hidden',
                    name: 'csrfmiddlewaretoken',
                    value: csrfToken
                }));
            }

            currentParams.forEach((value, key) => {
                $exportForm.append($('<input>', {
                    type: 'hidden',
                    name: key,
                    value: value
                }));
            });

            $exportForm.append($('<input>', {
                type: 'hidden',
                name: 'post',
                value: 'yes'
            }));

            $('body').append($exportForm);
            $exportForm.submit();
            $exportForm.remove();
        });

        // Счётчик выбранных
        function updateDeleteButton() {
            const count = $('input[name="_selected_action"]:checked').length;
            $('#count').text(count);
            $('#btn-delete').prop('disabled', count === 0);
        }

        $(document).on('change', 'input[name="_selected_action"]', updateDeleteButton);
        $(document).on('change', '#action-toggle', updateDeleteButton);
        updateDeleteButton();

        // Удаление
        $('#btn-delete').on('click', function (e) {
            e.preventDefault();
            const count = $('input[name="_selected_action"]:checked').length;

            if (count === 0) {
                alert('Выберите хотя бы одну заявку');
                return;
            }

            if (confirm('Удалить ' + count + ' заявок?')) {
                const $changelistForm = $('#changelist-form');

                if ($changelistForm.length === 0) {
                    alert('Ошибка: форма не найдена');
                    return;
                }

                let $actionSelect = $changelistForm.find('select[name="action"]');

                if ($actionSelect.length === 0) {
                    $changelistForm.append('<input type="hidden" name="action" value="delete_selected">');
                    $changelistForm.append('<input type="hidden" name="post" value="yes">');
                } else {
                    $actionSelect.val('delete_selected');
                }

                $changelistForm.submit();
            }
        });

        // Enter для применения фильтров
        $form.find('input[type="text"], input[type="date"]').on('keypress', function (e) {
            if (e.which === 13) {
                e.preventDefault();
                $form.submit();
            }
        });

        // ==================== АВТОСОХРАНЕНИЕ СТАТУСА/ПРИОРИТЕТА/МЕНЕДЖЕРА ====================
        const editableSelects = $('#changelist-form select').filter(function() {
            const name = $(this).attr('name') || '';
            return name.match(/priority|status|manager/);
        });

        editableSelects.each(function() {
            const select = $(this);
            const row = select.closest('tr');
            const checkbox = row.find('input[name="_selected_action"]');
            const objectId = checkbox.val();

            if (!objectId) return;

            select.data('original-value', select.val());

            select.on('change', function() {
                const newValue = $(this).val();
                const originalValue = select.data('original-value');
                
                let fieldName = '';
                const selectName = select.attr('name') || '';
                
                if (selectName.includes('priority')) fieldName = 'priority';
                else if (selectName.includes('status')) fieldName = 'status';
                else if (selectName.includes('manager')) fieldName = 'manager';

                if (!fieldName) return;

                const saveUrl = `/admin/main/contactform/${objectId}/quick-update/`;

                select.css({
                    'opacity': '0.5',
                    'pointer-events': 'none'
                });

                $.ajax({
                    url: saveUrl,
                    method: 'POST',
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
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initContactFormAdmin);
    } else {
        initContactFormAdmin();
    }
})();