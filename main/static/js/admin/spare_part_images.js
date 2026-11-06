/*** Фото запчастей: drag&drop и вставка из буфера (Ctrl+V) в инлайн "Фото запчасти" ***/

(function () {
    'use strict';

    var PREFIX = 'images';              // related_name у SparePartImage.part
    var MAX_SIZE = 5 * 1024 * 1024;     // как validate_image_size

    var group, zone, statusEl;

    window.addEventListener('load', function () {
        setTimeout(init, 300);
    });

    function init() {
        group = document.getElementById(PREFIX + '-group');
        if (!group || document.getElementById('spi-dropzone')) return;

        zone = document.createElement('div');
        zone.id = 'spi-dropzone';
        zone.className = 'spi-dropzone';
        zone.innerHTML =
            '<div class="spi-dropzone-title">Перетащите фото сюда или нажмите Ctrl+V</div>' +
            '<div class="spi-dropzone-hint">Файлы с компьютера, скриншоты, скопированные картинки. ' +
            'Можно сразу несколько. До 5 МБ каждое. Клик — выбрать файлы.</div>' +
            '<div class="spi-dropzone-status"></div>';
        statusEl = zone.querySelector('.spi-dropzone-status');
        group.parentNode.insertBefore(zone, group);

        var picker = document.createElement('input');
        picker.type = 'file';
        picker.accept = 'image/*';
        picker.multiple = true;
        picker.style.display = 'none';
        zone.appendChild(picker);
        zone.addEventListener('click', function (e) {
            if (e.target !== picker) picker.click();
        });
        picker.addEventListener('change', function () {
            addFiles(Array.prototype.slice.call(picker.files));
            picker.value = '';
        });

        // Drop ловим на всей странице: промахнулся мимо зоны — браузер
        // просто открыл бы картинку вместо страницы и форма бы потерялась.
        var depth = 0;
        document.addEventListener('dragenter', function (e) {
            if (!isRelevantDrag(e)) return;
            depth++;
            zone.classList.add('spi-active');
        });
        document.addEventListener('dragleave', function () {
            depth = Math.max(0, depth - 1);
            if (!depth) zone.classList.remove('spi-active');
        });
        document.addEventListener('dragover', function (e) {
            if (!isRelevantDrag(e)) return;
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });
        document.addEventListener('drop', function (e) {
            depth = 0;
            zone.classList.remove('spi-active');
            if (!isRelevantDrag(e)) return;
            e.preventDefault();
            addImageFiles(e.dataTransfer);
        });

        // Обычный текст оставляем полям ввода — перехватываем только картинки
        document.addEventListener('paste', function (e) {
            if (addImageFiles(e.clipboardData)) e.preventDefault();
        });

        // Превью и для файлов, выбранных штатной кнопкой в строке
        group.addEventListener('change', function (e) {
            if (e.target.type === 'file') showPreview(e.target);
        });
    }

    function isRelevantDrag(e) {
        var types = e.dataTransfer && e.dataTransfer.types;
        return !!types && Array.prototype.indexOf.call(types, 'Files') !== -1;
    }

    // Возвращает true, если среди файлов нашлись картинки
    function addImageFiles(dt) {
        var files = Array.prototype.filter.call((dt && dt.files) || [], function (f) {
            return f.type.indexOf('image/') === 0;
        });
        if (!files.length) return false;
        addFiles(files);
        return true;
    }

    function addFiles(files) {
        files.forEach(function (file) {
            if (file.type.indexOf('image/') !== 0) {
                showError('Не изображение: ' + file.name);
                return;
            }
            if (file.size > MAX_SIZE) {
                showError('Больше 5 МБ: ' + file.name);
                return;
            }
            // Скриншоты из буфера всегда называются image.png — даём уникальное имя
            if (/^image\.(png|jpe?g)$/i.test(file.name)) {
                file = new File([file], 'part-' + Date.now() + '-' +
                    Math.floor(Math.random() * 1000) + '.' + file.name.split('.').pop(), {type: file.type});
            }

            var row = getEmptyRow();
            if (!row) {
                showError('Достигнут лимит фото для запчасти');
                return;
            }
            var input = row.querySelector('input[type="file"]');
            var dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;

            var order = row.querySelector('input[name$="-order"]');
            if (order) order.value = nextOrder(order);

            showPreview(input);
        });
    }

    // Свободная строка инлайна: новая (без id) и без выбранного файла.
    // Если таких нет — жмём штатную "Добавить ещё".
    function getEmptyRow() {
        var row = findEmptyRow();
        if (row) return row;
        var addLink = group.querySelector('.add-row a');
        if (!addLink || addLink.offsetParent === null) return null;
        addLink.click();
        return findEmptyRow();
    }

    function findEmptyRow() {
        var rows = group.querySelectorAll('.dynamic-' + PREFIX + ', tr.form-row');
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            if (row.id === PREFIX + '-empty' || row.classList.contains('empty-form')) continue;
            var idInput = row.querySelector('input[name$="-id"]');
            var file = row.querySelector('input[type="file"]');
            if (!file || (idInput && idInput.value)) continue;
            if (!file.files.length) return row;
        }
        return null;
    }

    function nextOrder(current) {
        var max = -1;
        Array.prototype.forEach.call(group.querySelectorAll('input[name$="-order"]'), function (inp) {
            if (inp === current || inp.name.indexOf('__prefix__') !== -1) return;
            var v = parseInt(inp.value, 10);
            if (!isNaN(v) && v > max) max = v;
        });
        return max + 1;
    }

    function showPreview(input) {
        var cell = input.parentNode;
        var img = cell.querySelector('img.spi-preview');
        if (!input.files.length) {
            if (img) img.remove();
            return;
        }
        if (!img) {
            img = document.createElement('img');
            img.className = 'spi-preview';
            cell.appendChild(img);
        }
        if (img.dataset.url) URL.revokeObjectURL(img.dataset.url);
        img.dataset.url = URL.createObjectURL(input.files[0]);
        img.src = img.dataset.url;
    }

    function showError(msg) {
        var line = document.createElement('div');
        line.className = 'spi-error';
        line.textContent = msg;
        statusEl.appendChild(line);
        setTimeout(function () { line.remove(); }, 8000);
    }
})();
