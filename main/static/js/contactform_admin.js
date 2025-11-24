(function() {
    'use strict';
    
    console.log('=== ContactForm Admin Init ===');
    
    if (typeof window.django === 'undefined' || typeof window.django.jQuery === 'undefined') {
        console.error('jQuery not found');
        return;
    }
    
    const $ = window.django.jQuery;

    // ========== УБИРАЕМ e=1 ИЗ URL ==========
    (function removeEParam() {
        const url = new URL(window.location.href);
        if (url.searchParams.has('e')) {
            console.log('🔄 Found e=1, removing...');
            url.searchParams.delete('e');
            window.history.replaceState({}, '', url.toString());
            console.log('✅ Removed e=1 from URL');
        }
    })();

    $(document).ready(function() {
        console.log('DOM ready');
        
        const $form = $('#leads-filter-form');
        if ($form.length === 0) {
            console.error('Form #leads-filter-form not found');
            return;
        }
        
        console.log('Form found');

        // ==================== ПРИМЕНИТЬ ФИЛЬТРЫ ====================
        $form.on('submit', function(e) {
            e.preventDefault();
            
            const params = new URLSearchParams();
            
            $form.find('input, select').each(function() {
                const $field = $(this);
                const name = $field.attr('name');
                const value = $field.val();
                
                if (name && value && value.trim() !== '') {
                    params.append(name, value.trim());
                }
            });
            
            const queryString = params.toString();
            const newUrl = window.location.pathname + (queryString ? '?' + queryString : '');
            window.location.href = newUrl;
        });

        // ==================== СБРОС ====================
        $('#btn-reset').on('click', function(e) {
            e.preventDefault();
            window.location.href = window.location.pathname;
        });

        // ==================== ЭКСПОРТ ====================
        $('#btn-export').on('click', function(e) {
            e.preventDefault();
            
            const currentParams = new URLSearchParams(window.location.search);
            currentParams.delete('e');
            
            const selectedIds = [];
            $('input[name="_selected_action"]:checked').each(function() {
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

        // ==================== СЧЁТЧИК ====================
        function updateDeleteButton() {
            const count = $('input[name="_selected_action"]:checked').length;
            $('#count').text(count);
            $('#btn-delete').prop('disabled', count === 0);
        }

        $(document).on('change', 'input[name="_selected_action"]', updateDeleteButton);
        $(document).on('change', '#action-toggle', updateDeleteButton);
        updateDeleteButton();

        // ==================== УДАЛИТЬ ====================
        $('#btn-delete').on('click', function(e) {
            e.preventDefault();
            const count = $('input[name="_selected_action"]:checked').length;
            
            if (count === 0) {
                alert('Выберите хотя бы одну заявку');
                return;
            }
            
            if (confirm('Удалить ' + count + ' заявок?')) {
                const $changelistForm = $('#changelist-form');
                
                if ($changelistForm.length === 0) {
                    console.error('❌ Form #changelist-form not found');
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

        // ==================== ENTER ====================
        $form.find('input[type="text"], input[type="date"]').on('keypress', function(e) {
            if (e.which === 13) {
                e.preventDefault();
                $form.submit();
            }
        });
        
        console.log('✅ All handlers initialized');
    });
})();