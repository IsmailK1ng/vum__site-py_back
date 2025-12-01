(function () {
    'use strict';

    if (typeof window.django === 'undefined' || typeof window.django.jQuery === 'undefined') {
        return;
    }

    const $ = window.django.jQuery;

    $(document).ready(function () {
        const $form = $('#leads-filter-form');
        if ($form.length === 0) return;

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
    });
})();