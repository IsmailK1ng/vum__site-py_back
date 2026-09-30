/*** Кнопка "Показать пример JSON" рядом с полем импорта параметров ***/

(function () {
    'use strict';

    // Пример тянется с сервера (api/parameters-example/), а не хранится тут
    // захардкоженным — так он собирается прямо из ProductParameter.CATEGORY_CHOICES
    // и новая категория, добавленная в будущем, появится в примере сама.
    var EXAMPLE_URL = '/admin/main/product/api/parameters-example/';
    var exampleTextCache = null;

    window.addEventListener('load', function () {
        setTimeout(init, 300);
    });

    function init() {
        var $ = window.jQuery;
        if (!$) return;

        var $field = $('#id_parameters_json');
        if ($field.length === 0 || $('#pj-example-btn').length) return;

        var $btn = $('<button>', {
            id: 'pj-example-btn',
            type: 'button',
            text: 'Показать пример JSON',
            css: {
                marginBottom: '8px',
                padding: '6px 14px',
                background: '#215cf7',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '600'
            }
        });

        $btn.on('click', openModal);
        $field.before($btn).before($('<br>'));

        buildModal($);
    }

    function buildModal($) {
        if ($('#pj-example-modal').length) return;

        var $overlay = $('<div>', { id: 'pj-example-modal', 'class': 'pj-example-overlay' });
        var $box = $('<div>', { 'class': 'pj-example-box' });

        var $header = $('<div>', { 'class': 'pj-example-header' });
        $header.append($('<span>', { text: 'Пример JSON для импорта параметров' }));
        var $closeBtn = $('<button>', { type: 'button', text: '×', 'class': 'pj-example-close' });
        $closeBtn.on('click', closeModal);
        $header.append($closeBtn);

        var $pre = $('<pre>', { id: 'pj-example-pre', 'class': 'pj-example-pre', text: 'Загрузка...' });

        var $footer = $('<div>', { 'class': 'pj-example-footer' });
        var $copyBtn = $('<button>', {
            id: 'pj-example-copy', type: 'button', text: 'Копировать', 'class': 'pj-example-copy'
        });
        $copyBtn.on('click', function () {
            if (exampleTextCache) copyText(exampleTextCache, $copyBtn);
        });
        $footer.append($copyBtn);

        $box.append($header, $pre, $footer);
        $overlay.append($box);
        $('body').append($overlay);

        $overlay.on('click', function (e) {
            if (e.target === $overlay[0]) closeModal();
        });
        $(document).on('keydown', function (e) {
            if (e.key === 'Escape') closeModal();
        });
    }

    function openModal() {
        var $ = window.jQuery;
        $('#pj-example-modal').addClass('pj-example-open');
        loadExample($);
    }

    function loadExample($) {
        if (exampleTextCache) {
            $('#pj-example-pre').text(exampleTextCache);
            return;
        }
        $.ajax({
            url: EXAMPLE_URL,
            method: 'GET',
            dataType: 'json'
        }).done(function (data) {
            exampleTextCache = JSON.stringify(data, null, 2);
            $('#pj-example-pre').text(exampleTextCache);
        }).fail(function () {
            $('#pj-example-pre').text('Не удалось загрузить пример. Попробуйте ещё раз.');
        });
    }

    function closeModal() {
        window.jQuery('#pj-example-modal').removeClass('pj-example-open');
    }

    function copyText(text, $btn) {
        var restore = function () {
            setTimeout(function () { $btn.text('Копировать'); }, 1500);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function () {
                $btn.text('Скопировано!');
                restore();
            });
            return;
        }
        var $tmp = window.jQuery('<textarea>').val(text).appendTo('body').select();
        document.execCommand('copy');
        $tmp.remove();
        $btn.text('Скопировано!');
        restore();
    }
})();
