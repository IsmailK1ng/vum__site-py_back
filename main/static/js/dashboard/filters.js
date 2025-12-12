// main/static/js/dashboard/filters.js

const DashboardFilters = {
    
    /**
     * Инициализация фильтров
     */
    init: function() {
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
        
        // Кнопка экспорта Word
        const btnWord = document.getElementById('btn-export-word');
        if (btnWord) {
            btnWord.addEventListener('click', () => {
                this.exportWord();
            });
        }
        
        console.log('Filters: Готов!');
    },
    
    /**
     * Применить фильтры
     */
    applyFilters: function() {
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
        
        // Обновляем фильтры в приложении
        DashboardApp.currentFilters = filters;
        
        // Загружаем данные
        DashboardApp.loadData();
        
        // Обновляем URL (чтобы можно было скопировать ссылку)
        this.updateURL(filters);
    },
    
    /**
     * Сбросить фильтры
     */

    resetFilters: function() {
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
     * Обновить URL с параметрами
     */
    updateURL: function(filters) {
        const params = new URLSearchParams();
        
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                params.set(key, filters[key]);
            }
        });
        
        const newURL = window.location.pathname + '?' + params.toString();
        window.history.pushState({}, '', newURL);
    },
    
    /**
     * Экспорт в Excel
     */
    exportExcel: function() {
        console.log('Filters: Экспорт в Excel...');
        
        const params = new URLSearchParams(DashboardApp.currentFilters);
        const url = '/admin/dashboard/export/excel/?' + params.toString();
        
        window.open(url, '_blank');
    },
    
    /**
     * Экспорт в Word
     */
    exportWord: function() {
        console.log('Filters: Экспорт в Word...');
        
        const params = new URLSearchParams(DashboardApp.currentFilters);
        const url = '/admin/dashboard/export/word/?' + params.toString();
        
        window.open(url, '_blank');
    }
};