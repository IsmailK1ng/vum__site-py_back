// main/static/js/dashboard/filters.js

const DashboardFilters = {

    /**
     * Инициализация фильтров
     */
    init: function () {
        console.log('Filters: Инициализация...');

        // Обработчик формы
        const form = document.getElementById('dashboard-filters-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.applyFilters();
            });
        }

        // Кнопка сброса
        const btnReset = document.getElementById('btn-reset');
        if (btnReset) {
            btnReset.addEventListener('click', () => {
                this.resetFilters();
            });
        }

        // Кнопка экспорта Excel
        const btnExcel = document.getElementById('btn-export-excel');
        if (btnExcel) {
            btnExcel.addEventListener('click', () => {
                this.exportExcel();
            });
        }

        console.log('Filters: Готов!');
    },

    /**
     * Применить фильтры
     */

    applyFilters: function () {
        console.log('Filters: Применяем фильтры...');

        // Собираем данные из формы
        const filters = {
            date_from: document.getElementById('date_from').value,
            date_to: document.getElementById('date_to').value,
            region: document.getElementById('region').value,
            product: document.getElementById('product').value,
            source: document.getElementById('source').value
        };

        // Валидация дат
        if (!filters.date_from || !filters.date_to) {
            alert('Выберите период!');
            return;
        }

        const dateFrom = new Date(filters.date_from);
        const dateTo = new Date(filters.date_to);

        if (dateFrom > dateTo) {
            alert('Дата "от" не может быть позже даты "до"!');
            return;
        }

        // ✅ ПЕРЕЗАГРУЖАЕМ СТРАНИЦУ С ПАРАМЕТРАМИ
        const params = new URLSearchParams();

        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                params.set(key, filters[key]);
            }
        });

        window.location.href = window.location.pathname + '?' + params.toString();
    },

    /**
     * Сбросить фильтры
     */

    resetFilters: function () {
        console.log('Filters: Сброс фильтров...');

        // ✅ ОЧИЩАЕМ ВСЕ ПОЛЯ
        document.getElementById('date_from').value = '';
        document.getElementById('date_to').value = '';
        document.getElementById('region').value = '';
        document.getElementById('product').value = '';
        document.getElementById('source').value = '';

        // ✅ ПЕРЕЗАГРУЖАЕМ СТРАНИЦУ БЕЗ ПАРАМЕТРОВ
        window.location.href = '/admin/main/dashboard/';
    },


    /**
     * Экспорт в Excel
     */
    exportExcel: function () {
        console.log('Filters: Экспорт в Excel...');

        // ✅ БЕРЁМ ДАННЫЕ ИЗ ФОРМЫ, А НЕ ИЗ DashboardApp
        const filters = {
            date_from: document.getElementById('date_from').value,
            date_to: document.getElementById('date_to').value,
            region: document.getElementById('region').value,
            product: document.getElementById('product').value,
            source: document.getElementById('source').value
        };

        const params = new URLSearchParams();
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                params.set(key, filters[key]);
            }
        });

        const url = '/admin/main/dashboard/export/excel/?' + params.toString();
        window.open(url, '_blank');
    },
};