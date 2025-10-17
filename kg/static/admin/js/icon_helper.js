django.jQuery(document).ready(function($) {
    // Словарь переводов
    const translations = {
        'Дизель': { ky: 'Дизель', en: 'Diesel' },
        'кг': { ky: 'кг', en: 'kg' },
        'л.с.': { ky: 'а.к.', en: 'hp' },
        'м³': { ky: 'м³', en: 'm³' },
        'Климат-контроль': { ky: 'Климат-контроль', en: 'Climate control' },
        '4x2': { ky: '4x2', en: '4x2' },
        '4x4': { ky: '4x4', en: '4x4' },
        'Механика': { ky: 'Механикалык', en: 'Manual' },
        'Автомат': { ky: 'Автоматтык', en: 'Automatic' }
    };

    // Автозаполнение переводов при вводе RU
    $('input[name*="value_ru"]').on('blur', function() {
        const $row = $(this).closest('tr');
        const ruValue = $(this).val().trim();
        
        const $kyInput = $row.find('input[name*="value_ky"]');
        const $enInput = $row.find('input[name*="value_en"]');
        
        // Если поля пустые - заполняем автоматически
        if (!$kyInput.val() && !$enInput.val() && ruValue) {
            Object.keys(translations).forEach(ruTerm => {
                if (ruValue.includes(ruTerm)) {
                    const translated = translations[ruTerm];
                    
                    if (!$kyInput.val()) {
                        $kyInput.val(ruValue.replace(ruTerm, translated.ky));
                    }
                    if (!$enInput.val()) {
                        $enInput.val(ruValue.replace(ruTerm, translated.en));
                    }
                }
            });
        }
    });

    // Подсказка с галереей иконок
    $('.field-icon').each(function() {
        const $field = $(this);
        const helpHtml = `
            <div class="help">
                <strong>💡 Доступные иконки:</strong>
                <div class="icon-gallery">
                    <div class="icon-option" data-icon="engine.png">
                        <img src="/media/kg_vehicles/card_icons/engine.png">
                        <span>Двигатель</span>
                    </div>
                    <div class="icon-option" data-icon="fuel.png">
                        <img src="/media/kg_vehicles/card_icons/fuel.png">
                        <span>Топливо</span>
                    </div>
                    <div class="icon-option" data-icon="weight.png">
                        <img src="/media/kg_vehicles/card_icons/weight.png">
                        <span>Вес</span>
                    </div>
                    <div class="icon-option" data-icon="climate.png">
                        <img src="/media/kg_vehicles/card_icons/climate.png">
                        <span>Климат</span>
                    </div>
                    <div class="icon-option" data-icon="drive.png">
                        <img src="/media/kg_vehicles/card_icons/drive.png">
                        <span>Привод</span>
                    </div>
                </div>
                <p style="margin-top: 10px; font-size: 12px; color: #666;">
                    <strong>Автоперевод:</strong> При вводе "Дизель", "кг", "л.с." переводы заполнятся автоматически
                </p>
            </div>
        `;
        
        $field.append(helpHtml);
        
        // Клик по иконке - копирование имени файла
        $field.find('.icon-option').click(function() {
            const iconName = $(this).data('icon');
            const $input = $field.find('input[type="file"]');
            alert(`Загрузите файл: ${iconName}`);
        });
    });
});