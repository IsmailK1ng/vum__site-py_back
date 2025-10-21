(function() {
    'use strict';
    
    document.addEventListener('DOMContentLoaded', function() {
        
        const specsContainer = document.querySelector('.specs-container');
        if (!specsContainer) {
            return;
        }
        
        // Определяем секции
        const sections = [
            { 
                start: 'wheel_formula', 
                title: 'ОСНОВНЫЕ ХАРАКТЕРИСТИКИ', 
                fields: ['wheel_formula', 'dimensions_ru', 'dimensions_ky', 'dimensions_en', 
                        'wheelbase', 'fuel_type_ru', 'fuel_type_ky', 'fuel_type_en', 'tank_volume'] 
            },
            { 
                start: 'curb_weight', 
                title: 'ВЕСОВЫЕ ХАРАКТЕРИСТИКИ', 
                fields: ['curb_weight', 'payload', 'gross_weight'] 
            },
            { 
                start: 'body_type_ru', 
                title: 'КУЗОВ', 
                fields: ['body_type_ru', 'body_type_ky', 'body_type_en', 'body_dimensions_ru', 
                        'body_dimensions_ky', 'body_dimensions_en', 'body_volume', 
                        'body_material_ru', 'body_material_ky', 'body_material_en', 
                        'loading_type_ru', 'loading_type_ky', 'loading_type_en'] 
            },
            { 
                start: 'engine_model', 
                title: 'ДВИГАТЕЛЬ', 
                fields: ['engine_model', 'engine_volume', 'engine_power'] 
            },
            { 
                start: 'transmission_model', 
                title: 'ТРАНСМИССИЯ', 
                fields: ['transmission_model', 'transmission_type_ru', 'transmission_type_ky', 
                        'transmission_type_en', 'gears'] 
            },
            { 
                start: 'tire_type', 
                title: 'ШИНЫ И ТОРМОЗНАЯ СИСТЕМА', 
                fields: ['tire_type', 'suspension_ru', 'suspension_ky', 'suspension_en', 
                        'brakes_ru', 'brakes_ky', 'brakes_en'] 
            },
            { 
                start: 'cabin_category_ru', 
                title: 'КАБИНА', 
                fields: ['cabin_category_ru', 'cabin_category_ky', 'cabin_category_en', 
                        'cabin_equipment_ru', 'cabin_equipment_ky', 'cabin_equipment_en'] 
            }
        ];
        
        sections.forEach((section, index) => {
            const startField = specsContainer.querySelector('.field-' + section.start);
            if (!startField) {
                return;
            }
            
            // Создаем заголовок
            const header = document.createElement('div');
            header.className = 'section-header';
            header.textContent = section.title;
            header.dataset.section = index;
            
            // Создаем контейнер для полей
            const content = document.createElement('div');
            content.className = 'section-content';
            content.dataset.section = index;
            
            // Вставляем заголовок перед первым полем
            startField.parentNode.insertBefore(header, startField);
            startField.parentNode.insertBefore(content, header.nextSibling);
            
            // Перемещаем поля в контейнер
            section.fields.forEach(fieldName => {
                const field = specsContainer.querySelector('.field-' + fieldName);
                if (field) {
                    content.appendChild(field);
                }
            });
            
            // Обработчик клика
            header.addEventListener('click', function() {
                const isActive = this.classList.contains('active');
    
                // Закрываем все секции
                specsContainer.querySelectorAll('.section-header').forEach(h => h.classList.remove('active'));
                specsContainer.querySelectorAll('.section-content').forEach(c => c.classList.remove('active'));
                
                // Открываем текущую, если она была закрыта
                if (!isActive) {
                    this.classList.add('active');
                    content.classList.add('active');
                    
                    // Плавная прокрутка
                    setTimeout(() => {
                        content.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }, 300);
                }
            });
        });
        
        // Открываем первую секцию по умолчанию
        const firstHeader = specsContainer.querySelector('.section-header');
        if (firstHeader) {
            firstHeader.click();
        }
    });
})();
