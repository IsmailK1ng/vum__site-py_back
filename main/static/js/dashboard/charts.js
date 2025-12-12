// main/static/js/dashboard/charts.js

const DashboardCharts = {
    charts: {},
    
    /**
     * Инициализация
     */
    init: function() {
        console.log('Charts: Инициализация...');
        
        // Настройки Chart.js по умолчанию
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        Chart.defaults.font.size = 13;
        Chart.defaults.color = '#6b7280';
        
        console.log('Charts: Готов!');
    },
    
    /**
     * Отрисовать все графики
     */
    renderAll: function(data) {
        console.log('Charts: Отрисовка всех графиков...', data);
        
        // Уничтожаем старые графики
        this.destroyAll();
        
        // Отрисовываем новые
        this.renderDynamics(data.dynamics);
        this.renderSources(data.sources);
        this.renderModels(data.top_models);
        this.renderRegions(data.top_regions);
        this.renderHeatmap(data.heatmap);
    },
    
    /**
     * Уничтожить все графики
     */
    destroyAll: function() {
        Object.keys(this.charts).forEach(key => {
            if (this.charts[key]) {
                this.charts[key].destroy();
            }
        });
        this.charts = {};
    },
    
    /**
     * График: Динамика по дням
     */
    renderDynamics: function(data) {
        const ctx = document.getElementById('chart-dynamics');
        if (!ctx) return;
        
        this.charts.dynamics = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Текущий период',
                        data: data.current,
                        borderColor: '#1e57eb',
                        backgroundColor: 'rgba(30, 87, 235, 0.1)',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#1e57eb',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    },
                    {
                        label: 'Предыдущий период',
                        data: data.previous,
                        borderColor: '#9ca3af',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.4,
                        fill: false,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#9ca3af',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                weight: 600
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y + ' заявок';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    },
    
    /**
     * График: Источники трафика (круговая диаграмма)
     */
    renderSources: function(data) {
        const ctx = document.getElementById('chart-sources');
        if (!ctx) return;
        
        this.charts.sources = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: [
                        '#1e57eb', // Google - синий
                        '#e4405f', // Instagram - розовый
                        '#1877f2', // Facebook - синий FB
                        '#10b981', // Прямые - зелёный
                        '#f59e0b'  // Другие - оранжевый
                    ],
                    borderWidth: 2,
                    borderColor: '#fff',
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'right',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 13,
                                weight: 600
                            },
                            generateLabels: function(chart) {
                                const data = chart.data;
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const percent = ((value / data.datasets[0].data.reduce((a, b) => a + b, 0)) * 100).toFixed(1);
                                    return {
                                        text: `${label} (${percent}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percent = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} заявок (${percent}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    },
    
    /**
     * График: Топ моделей (горизонтальная диаграмма)
     */
    renderModels: function(data) {
        const ctx = document.getElementById('chart-models');
        if (!ctx) return;
        
        this.charts.models = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Заявок',
                    data: data.values,
                    backgroundColor: 'rgba(30, 87, 235, 0.8)',
                    borderColor: '#1e57eb',
                    borderWidth: 2,
                    borderRadius: 6,
                    barThickness: 30
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.x;
                                const index = context.dataIndex;
                                const percent = data.percentages[index];
                                return `${value} заявок (${percent}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                weight: 600
                            }
                        }
                    }
                }
            }
        });
    },
    
    /**
     * График: Топ регионов (столбчатая диаграмма)
     */
    renderRegions: function(data) {
        const ctx = document.getElementById('chart-regions');
        if (!ctx) return;
        
        this.charts.regions = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Заявок',
                    data: data.values,
                    backgroundColor: [
                        '#1e57eb',
                        '#3b82f6',
                        '#60a5fa',
                        '#93c5fd',
                        '#dbeafe'
                    ],
                    borderColor: '#1e57eb',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                const index = context.dataIndex;
                                const percent = data.percentages[index];
                                return `${value} заявок (${percent}%)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                weight: 600
                            }
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Тепловая карта: День × Час
     */
    renderHeatmap: function(data) {
        const container = document.getElementById('heatmap-container');
        if (!container) return;
        
        // Создаём HTML таблицу
        let html = '<table class="heatmap-table"><thead><tr><th></th>';
        
        // Заголовки часов
        data.hours.forEach(hour => {
            html += `<th>${hour}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        // Строки с днями
        data.data.forEach((row, dayIndex) => {
            html += `<tr><th>${data.weekdays[dayIndex]}</th>`;
            
            row.forEach((value, hourIndex) => {
                // Определяем интенсивность (0-5)
                const intensity = Math.min(5, Math.floor((value / data.max_value) * 5));
                
                html += `<td class="heatmap-cell" 
                            data-intensity="${intensity}" 
                            data-day="${data.weekdays[dayIndex]}" 
                            data-hour="${data.hours[hourIndex]}"
                            title="${data.weekdays[dayIndex]} ${data.hours[hourIndex]}: ${value} заявок">
                            ${value > 0 ? value : ''}
                        </td>`;
            });
            
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        
        // Добавляем легенду
        html += `
            <div class="heatmap-legend">
                <span>Интенсивность:</span>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f9fafb;"></div>
                    <span>0</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #dbeafe;"></div>
                    <span>Низкая</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #93c5fd;"></div>
                    <span>Средняя</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #3b82f6;"></div>
                    <span>Высокая</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #1e40af;"></div>
                    <span>Очень высокая</span>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
};