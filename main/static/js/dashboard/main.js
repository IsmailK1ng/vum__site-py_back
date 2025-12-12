// main/static/js/dashboard/main.js

const DashboardApp = {
    currentFilters: {},
    charts: {},

    /**
     * Инициализация Dashboard
     */
    init: function (initialFilters) {
        console.log('Dashboard: Инициализация...');

        this.currentFilters = initialFilters;

        // Инициализируем модули
        DashboardFilters.init();
        DashboardAPI.init();
        DashboardCharts.init();

        // Загружаем данные
        this.loadData();

        // Инициализируем вкладки таблиц
        this.initTabs();

        console.log('Dashboard: Готов!');
    },

    /**
     * Загрузка данных
     */
    loadData: function () {
        console.log('Dashboard: Загрузка данных...', this.currentFilters);

        // Показываем индикаторы загрузки
        this.showLoading();

        // Запрашиваем данные через API
        DashboardAPI.getData(this.currentFilters)
            .then(data => {
                console.log('Dashboard: Данные получены', data);
                this.renderData(data);
                this.hideLoading();
            })
            .catch(error => {
                console.error('Dashboard: Ошибка загрузки данных', error);
                this.showError('Ошибка загрузки данных. Попробуйте обновить страницу.');
                this.hideLoading();
            });
    },

    /**
     * Отрисовка данных
     */
    renderData: function (data) {
        // 1. KPI метрики
        this.renderKPI(data.kpi);

        // 2. Графики
        DashboardCharts.renderAll(data.charts);

        // 3. Таблицы
        this.renderTables(data.charts);

        // 4. Инсайты
        this.renderInsights(data.insights);
    },

    /**
     * Отрисовка KPI
     */
    renderKPI: function (kpi) {
        // Всего заявок
        const totalElement = document.getElementById('kpi-total');
        if (totalElement) {
            totalElement.textContent = kpi.total_leads.toLocaleString('ru-RU');
        }

        // Конверсия amoCRM
        const conversionElement = document.getElementById('kpi-conversion');
        if (conversionElement) {
            conversionElement.textContent = kpi.amocrm_conversion + '%';
        }

        const conversionDetailsElement = document.getElementById('kpi-conversion-details');
        if (conversionDetailsElement) {
            conversionDetailsElement.textContent = `${kpi.amocrm_sent} из ${kpi.total_leads}`;
        }

        // Средняя скорость
        const speedElement = document.getElementById('kpi-speed');
        if (speedElement) {
            speedElement.textContent = kpi.avg_response_time + ' мин';
        }

        // Тренд
        const trendValue = kpi.trend.value;
        const trendDirection = kpi.trend.direction;
        const trendIcon = document.getElementById('trend-icon');
        const trendElement = document.getElementById('kpi-trend');

        if (trendElement) {
            trendElement.textContent = (trendValue > 0 ? '+' : '') + trendValue + '%';

            // Убираем старые классы
            trendElement.classList.remove('up', 'down');

            // Добавляем новые
            if (trendDirection === 'up') {
                trendElement.classList.add('up');
            } else if (trendDirection === 'down') {
                trendElement.classList.add('down');
            }
        }

        if (trendIcon) {
            trendIcon.classList.remove('up', 'down');

            if (trendDirection === 'up') {
                trendIcon.textContent = '📈';
                trendIcon.classList.add('up');
            } else if (trendDirection === 'down') {
                trendIcon.textContent = '📉';
                trendIcon.classList.add('down');
            } else {
                trendIcon.textContent = '➡️';
            }
        }
    },

    /**
     * Отрисовка таблиц
     */

    renderTables: function (charts) {
        console.log('Dashboard: Отрисовка таблиц', charts);

        // 1. Таблица источников (уже работает)
        this.renderSourcesTable(charts.sources);

        // 2. Таблица моделей (уже работает)
        this.renderModelsTable(charts.top_models);

        // 3. Таблица регионов (уже работает)
        this.renderRegionsTable(charts.top_regions);

        // 4. Временной анализ
        if (charts.time_analysis) {
            this.renderTimeAnalysisTables(charts.time_analysis);
        }

        // 5. UTM кампании
        if (charts.utm_campaigns) {
            this.renderUTMTable(charts.utm_campaigns);
        }

        // 6. Referer
        if (charts.referer_data) {
            this.renderRefererTable(charts.referer_data);
        }

        // 7. Матрицы
        if (charts.region_model_matrix && charts.source_model_matrix) {
            this.renderMatrices(charts.region_model_matrix, charts.source_model_matrix);
        }

        // 8. Поведение клиентов
        if (charts.behavior) {
            this.renderBehaviorData(charts.behavior);
        }
    },

    /**
     * Таблица источников
     */
    renderSourcesTable: function (sources) {
        const tbody = document.getElementById('table-sources-body');
        if (!tbody || !sources) {
            console.log('Таблица источников: элемент не найден');
            return;
        }

        let html = '';

        sources.labels.forEach((label, index) => {
            const value = sources.values[index];
            const percent = sources.percentages[index];

            // Имитация данных (конверсия и время)
            const conversion = Math.floor(85 + Math.random() * 10);
            const avgTime = Math.floor(8 + Math.random() * 10);

            html += `
                <tr>
                    <td><strong>${label}</strong></td>
                    <td>${value}</td>
                    <td>${Math.floor(value * conversion / 100)}</td>
                    <td>${conversion}%</td>
                    <td>${avgTime} мин</td>
                    <td><span class="trend-badge up">+5%</span></td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
        console.log('Таблица источников: отрисована');
    },

    /**
     * Таблица моделей
     */
    renderModelsTable: function (models) {
        const tbody = document.getElementById('table-models-body');
        if (!tbody || !models) {
            console.log('Таблица моделей: элемент не найден');
            return;
        }

        let html = '';

        models.labels.forEach((label, index) => {
            const value = models.values[index];
            const percent = models.percentages[index];

            // Имитация предыдущего периода
            const prevValue = Math.floor(value * (0.8 + Math.random() * 0.4));
            const change = value - prevValue;
            const changePercent = prevValue > 0 ? Math.floor((change / prevValue) * 100) : 0;

            const trendClass = change > 0 ? 'up' : change < 0 ? 'down' : 'neutral';
            const trendSymbol = change > 0 ? '↗' : change < 0 ? '↘' : '→';

            html += `
                <tr>
                    <td><strong>${label}</strong></td>
                    <td>${value}</td>
                    <td>${prevValue}</td>
                    <td><span class="trend-badge ${trendClass}">${change > 0 ? '+' : ''}${change} (${changePercent}%) ${trendSymbol}</span></td>
                    <td>Google (${Math.floor(value * 0.4)})</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
        console.log('Таблица моделей: отрисована');
    },

    /**
     * Таблица регионов
     */
    renderRegionsTable: function (regions) {
        const tbody = document.getElementById('table-regions-body');
        if (!tbody || !regions) {
            console.log('Таблица регионов: элемент не найден');
            return;
        }

        let html = '';

        regions.labels.forEach((label, index) => {
            const value = regions.values[index];
            const percent = regions.percentages[index];

            const prevValue = Math.floor(value * (0.85 + Math.random() * 0.3));
            const change = value - prevValue;
            const changePercent = prevValue > 0 ? Math.floor((change / prevValue) * 100) : 0;

            const trendClass = change > 0 ? 'up' : change < 0 ? 'down' : 'neutral';
            const trendSymbol = change > 0 ? '↗' : change < 0 ? '↘' : '→';

            html += `
                <tr>
                    <td><strong>${label}</strong></td>
                    <td>${value}</td>
                    <td>${prevValue}</td>
                    <td><span class="trend-badge ${trendClass}">${change > 0 ? '+' : ''}${change} (${changePercent}%) ${trendSymbol}</span></td>
                    <td>—</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
        console.log('Таблица регионов: отрисована');
    },


    /**
     * Отрисовка инсайтов
     */
    renderInsights: function (insights) {
        const container = document.getElementById('insights-content');
        if (!container) return;

        if (!insights) {
            container.innerHTML = '<p class="loading">Нет данных для анализа</p>';
            return;
        }

        let html = '';

        // Что работает хорошо
        if (insights.good && insights.good.length > 0) {
            html += `
                <div class="insight-section good">
                    <h4>✅ Что работает хорошо</h4>
                    <ul>
                        ${insights.good.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Проблемы
        if (insights.problems && insights.problems.length > 0) {
            html += `
                <div class="insight-section problems">
                    <h4>⚠️ Проблемы и возможности</h4>
                    <ul>
                        ${insights.problems.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Рекомендации
        if (insights.recommendations && insights.recommendations.length > 0) {
            html += `
                <div class="insight-section recommendations">
                    <h4>🎯 Рекомендации</h4>
                    <ul>
                        ${insights.recommendations.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (html === '') {
            html = '<p class="loading">Нет данных для анализа</p>';
        }

        container.innerHTML = html;
    },

    /**
     * Инициализация вкладок
     */
    initTabs: function () {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const tabName = this.dataset.tab;
                const parent = this.closest('.table-card');

                if (!parent) return;

                // Убираем активность со всех вкладок
                parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                parent.querySelectorAll('.table-content').forEach(c => c.classList.add('hidden'));

                // Активируем выбранную
                this.classList.add('active');
                const targetTab = parent.querySelector(`#tab-${tabName}`);
                if (targetTab) {
                    targetTab.classList.remove('hidden');
                }
            });
        });
    },
    /**
 * Временной анализ: по часам и дням
 */
    renderTimeAnalysisTables: function (data) {
        // Таблица по часам
        const hoursBody = document.getElementById('table-hours-body');
        if (hoursBody && data.by_hours) {
            let html = '';
            data.by_hours.forEach(item => {
                html += `
                <tr>
                    <td><strong>${item.hour}</strong></td>
                    <td>${item.count}</td>
                    <td>${item.percent}%</td>
                    <td>${item.top_model}</td>
                    <td>${item.avg_time} мин</td>
                </tr>
            `;
            });
            hoursBody.innerHTML = html;
        }

        // Таблица по дням недели
        const weekdaysBody = document.getElementById('table-weekdays-body');
        if (weekdaysBody && data.by_weekdays) {
            let html = '';
            data.by_weekdays.forEach(item => {
                html += `
                <tr>
                    <td><strong>${item.day}</strong></td>
                    <td>${item.count}</td>
                    <td>${item.percent}%</td>
                    <td>${item.top_hour}</td>
                    <td>${item.avg_time} мин</td>
                </tr>
            `;
            });
            weekdaysBody.innerHTML = html;
        }

        console.log('Временной анализ: отрисован');
    },

    /**
     * UTM кампании
     */
    renderUTMTable: function (campaigns) {
        const tbody = document.getElementById('table-utm-body');
        if (!tbody || !campaigns || campaigns.length === 0) {
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="6">Нет данных</td></tr>';
            }
            return;
        }

        let html = '';
        campaigns.forEach(item => {
            html += `
            <tr>
                <td><strong>${item.source}</strong></td>
                <td>${item.medium}</td>
                <td>${item.campaign}</td>
                <td>${item.count}</td>
                <td>—</td>
                <td>—</td>
            </tr>
        `;
        });

        tbody.innerHTML = html;
        console.log('UTM кампании: отрисованы');
    },

    /**
     * Referer данные
     */
    renderRefererTable: function (referers) {
        const tbody = document.getElementById('table-referer-body');
        if (!tbody || !referers || referers.length === 0) {
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="4">Нет данных</td></tr>';
            }
            return;
        }

        let html = '';
        referers.forEach(item => {
            html += `
            <tr>
                <td><strong>${item.referer}</strong></td>
                <td>${item.count}</td>
                <td>${item.percent}%</td>
                <td><div style="width:${item.percent}%;height:8px;background:#1e57eb;border-radius:4px;"></div></td>
            </tr>
        `;
        });

        tbody.innerHTML = html;
        console.log('Referer: отрисован');
    },

    /**
     * Матрицы Регион×Модель и Источник×Модель
     */
    renderMatrices: function (regionMatrix, sourceMatrix) {
        // Регион × Модель
        const regionContainer = document.getElementById('matrix-region-model');
        if (regionContainer && regionMatrix) {
            let html = '<table class="matrix-table"><thead><tr><th>Регион / Модель</th>';

            regionMatrix.models.forEach(model => {
                html += `<th>${model.substring(0, 20)}...</th>`;
            });
            html += '</tr></thead><tbody>';

            regionMatrix.regions.forEach((region, idx) => {
                html += `<tr><td><strong>${region}</strong></td>`;
                regionMatrix.data[idx].forEach(value => {
                    const color = value > 0 ? `rgba(30, 87, 235, ${Math.min(value / 10, 1)})` : '#f5f5f5';
                    html += `<td style="background:${color};text-align:center;">${value}</td>`;
                });
                html += '</tr>';
            });

            html += '</tbody></table>';
            regionContainer.innerHTML = html;
        }

        // Источник × Модель
        const sourceContainer = document.getElementById('matrix-source-model');
        if (sourceContainer && sourceMatrix) {
            let html = '<table class="matrix-table"><thead><tr><th>Источник / Модель</th>';

            sourceMatrix.models.forEach(model => {
                html += `<th>${model.substring(0, 20)}...</th>`;
            });
            html += '</tr></thead><tbody>';

            sourceMatrix.sources.forEach((source, idx) => {
                html += `<tr><td><strong>${source}</strong></td>`;
                sourceMatrix.data[idx].forEach(value => {
                    const color = value > 0 ? `rgba(16, 185, 129, ${Math.min(value / 10, 1)})` : '#f5f5f5';
                    html += `<td style="background:${color};text-align:center;">${value}</td>`;
                });
                html += '</tr>';
            });

            html += '</tbody></table>';
            sourceContainer.innerHTML = html;
        }

        console.log('Матрицы: отрисованы');
    },

    /**
     * Поведение клиентов
     */
    renderBehaviorData: function (behavior) {
        // Статистика
        const statsContainer = document.getElementById('behavior-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
            <div class="behavior-stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${behavior.total_leads}</div>
                    <div class="stat-label">Всего заявок</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${behavior.unique_clients}</div>
                    <div class="stat-label">Уникальных клиентов</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${behavior.repeat_clients}</div>
                    <div class="stat-label">Повторных обращений</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${behavior.repeat_percent}%</div>
                    <div class="stat-label">Процент повторных</div>
                </div>
            </div>
        `;
        }

        // Таблица повторных клиентов
        const transitionsBody = document.getElementById('table-transitions-body');
        if (transitionsBody && behavior.clients_list) {
            if (behavior.clients_list.length === 0) {
                transitionsBody.innerHTML = '<tr><td colspan="3">Нет повторных клиентов</td></tr>';
            } else {
                let html = '';
                behavior.clients_list.forEach(client => {
                    html += `
                    <tr>
                        <td><strong>${client.name}</strong><br><small>${client.phone}</small></td>
                        <td>${client.count} заявок<br><small>${client.models}</small></td>
                        <td>${client.interval_days} дней<br><small>Последняя: ${client.last_date}</small></td>
                    </tr>
                `;
                });
                transitionsBody.innerHTML = html;
            }
        }

        console.log('Поведение клиентов: отрисовано');
    },

    /**
     * Показать индикаторы загрузки
     */
    showLoading: function () {
        // KPI
        document.querySelectorAll('.kpi-value').forEach(el => {
            el.textContent = '—';
        });

        // Инсайты
        const insightsContent = document.getElementById('insights-content');
        if (insightsContent) {
            insightsContent.innerHTML = '<p class="loading">Загрузка рекомендаций...</p>';
        }
    },

    /**
     * Скрыть индикаторы загрузки
     */
    hideLoading: function () {
        // Убираем все .loading элементы
        document.querySelectorAll('.loading').forEach(el => {
            if (el.textContent === 'Загрузка...') {
                el.textContent = 'Данные загружены';
            }
        });
    },

    /**
     * Показать ошибку
     */
    showError: function (message) {
        alert('Ошибка: ' + message);
    }
};