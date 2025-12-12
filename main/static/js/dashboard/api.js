// main/static/js/dashboard/api.js

const DashboardAPI = {
    
    /**
     * Инициализация
     */
    init: function() {
        console.log('API: Инициализация...');
        
        // Получаем CSRF токен
        this.csrfToken = this.getCSRFToken();
        
        console.log('API: Готов!');
    },
    
    /**
     * Получить CSRF токен
     */
    getCSRFToken: function() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return null;
    },
    
    /**
     * Получить данные Dashboard
     */
    getData: function(filters) {
        return new Promise((resolve, reject) => {
            const params = new URLSearchParams(filters);
            const url = `/admin/main/dashboard/api/data/?${params}`;
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Генерируем инсайты на основе данных
                    data.insights = this.generateInsights(data.kpi, data.charts);
                    resolve(data);
                } else {
                    reject(new Error(data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('API Error:', error);
                reject(error);
            });
        });
    },
    
    /**
     * Генерация инсайтов (временная функция, потом перенесём на backend)
     */
    generateInsights: function(kpi, charts) {
        const insights = {
            good: [],
            problems: [],
            recommendations: []
        };
        
        // Анализ конверсии
        if (kpi.amocrm_conversion >= 90) {
            insights.good.push(`Отличная конверсия в amoCRM — ${kpi.amocrm_conversion}%`);
        } else if (kpi.amocrm_conversion < 80) {
            insights.problems.push(`Низкая конверсия в amoCRM — ${kpi.amocrm_conversion}% (ниже среднего)`);
            insights.recommendations.push('Проверить качество лидов и настройки интеграции с amoCRM');
        }
        
        // Анализ тренда
        if (kpi.trend.direction === 'up') {
            insights.good.push(`Позитивная динамика: +${kpi.trend.value}% к предыдущему периоду`);
        } else if (kpi.trend.direction === 'down') {
            insights.problems.push(`Падение заявок: ${kpi.trend.value}% к предыдущему периоду`);
            insights.recommendations.push('Усилить маркетинговые активности');
        }
        
        // Анализ источников
        if (charts.sources && charts.sources.values) {
            const maxSource = Math.max(...charts.sources.values);
            const maxIndex = charts.sources.values.indexOf(maxSource);
            const sourceName = charts.sources.labels[maxIndex];
            const percent = charts.sources.percentages[maxIndex];
            
            if (percent > 50) {
                insights.problems.push(`Высокая зависимость от ${sourceName} (${percent}%)`);
                insights.recommendations.push('Диверсифицировать источники трафика');
            } else {
                insights.good.push(`${sourceName} — основной источник (${percent}%)`);
            }
        }
        
        // Анализ моделей
        if (charts.top_models && charts.top_models.labels.length > 0) {
            const topModel = charts.top_models.labels[0];
            const topPercent = charts.top_models.percentages[0];
            
            insights.good.push(`${topModel} — самая популярная модель (${topPercent}%)`);
            insights.recommendations.push(`Запустить дополнительную кампанию для ${topModel}`);
        }
        
        return insights;
    }
};