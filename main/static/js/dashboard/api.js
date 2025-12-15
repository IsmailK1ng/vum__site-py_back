// main/static/js/dashboard/api.js

const DashboardAPI = {

    /**
     * Инициализация
     */
    init: function () {
        console.log('API: Инициализация...');

        // Получаем CSRF токен
        this.csrfToken = this.getCSRFToken();

        console.log('API: Готов!');
    },
    /**
     * Загрузить список продуктов
     */
    loadProducts: function () {
        fetch('/admin/main/dashboard/api/products/')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('product');
                if (select && data.products) {
                    // ✅ СОХРАНЯЕМ ТЕКУЩЕЕ ЗНАЧЕНИЕ
                    const currentValue = select.value;

                    // ✅ НЕ ТРОГАЕМ ПЕРВУЮ ОПЦИЮ "Все модели"
                    // Удаляем только старые продукты (если есть)
                    while (select.options.length > 1) {
                        select.remove(1);
                    }

                    // Добавляем новые продукты
                    data.products.forEach(product => {
                        const option = document.createElement('option');
                        option.value = product;
                        option.textContent = product;

                        // ✅ ВОССТАНАВЛИВАЕМ ВЫБРАННОЕ ЗНАЧЕНИЕ
                        if (product === currentValue) {
                            option.selected = true;
                        }

                        select.appendChild(option);
                    });

                    // ✅ ЕСЛИ БЫЛО ВЫБРАНО ЗНАЧЕНИЕ — ВОССТАНАВЛИВАЕМ
                    if (currentValue) {
                        select.value = currentValue;
                    }
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки продуктов:', error);
            });
    },

    /**
     * Получить CSRF токен
     */
    getCSRFToken: function () {
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
    getData: function (filters) {
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
    }
};