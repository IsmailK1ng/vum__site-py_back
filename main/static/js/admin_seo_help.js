/**
 * SEO ПАНЕЛЬ - JavaScript для tooltip с иконками помощи
 */

(function() {
    'use strict';
    
    // Создаем единый контейнер для tooltip
    let tooltipElement = null;
    
    function createTooltip() {
        if (tooltipElement) return tooltipElement;
        
        tooltipElement = document.createElement('div');
        tooltipElement.className = 'seo-help-tooltip';
        document.body.appendChild(tooltipElement);
        
        return tooltipElement;
    }
    
    function showTooltip(icon, htmlContent) {
        const tooltip = createTooltip();
        
        // Устанавливаем HTML контент
        tooltip.innerHTML = htmlContent;
        
        // Показываем tooltip
        tooltip.classList.add('visible');
        
        // Позиционируем
        const iconRect = icon.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        // Позиция: над иконкой, по центру
        let left = iconRect.left + (iconRect.width / 2) - (tooltipRect.width / 2);
        let top = iconRect.top - tooltipRect.height - 12;
        
        // Проверяем, не выходит ли за пределы экрана
        if (left < 10) left = 10;
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = window.innerWidth - tooltipRect.width - 10;
        }
        
        if (top < 10) {
            // Если не помещается сверху, показываем снизу
            top = iconRect.bottom + 12;
            tooltip.style.top = top + 'px';
            
            // Меняем направление стрелки
            tooltip.classList.add('arrow-top');
        } else {
            tooltip.style.top = top + 'px';
            tooltip.classList.remove('arrow-top');
        }
        
        tooltip.style.left = left + 'px';
    }
    
    function hideTooltip() {
        if (tooltipElement) {
            tooltipElement.classList.remove('visible');
        }
    }
    
    function initHelpIcons() {
        const icons = document.querySelectorAll('.seo-help-icon');
        
        icons.forEach(icon => {
            // Убираем старые обработчики
            icon.replaceWith(icon.cloneNode(true));
        });
        
        // Добавляем новые обработчики
        document.querySelectorAll('.seo-help-icon').forEach(icon => {
            const helpText = icon.getAttribute('data-help');
            
            if (!helpText) return;
            
            icon.addEventListener('mouseenter', function() {
                showTooltip(this, helpText);
            });
            
            icon.addEventListener('mouseleave', function() {
                hideTooltip();
            });
            
            // На мобильных - по клику
            icon.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                if (tooltipElement && tooltipElement.classList.contains('visible')) {
                    hideTooltip();
                } else {
                    showTooltip(this, helpText);
                }
            });
        });
        
        // Закрытие при клике вне tooltip
        document.addEventListener('click', function(e) {
            if (tooltipElement && 
                !tooltipElement.contains(e.target) && 
                !e.target.closest('.seo-help-icon')) {
                hideTooltip();
            }
        });
        
        // Закрытие при прокрутке
        window.addEventListener('scroll', hideTooltip);
    }
    
    // Инициализация при загрузке страницы
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initHelpIcons);
    } else {
        initHelpIcons();
    }
    
    // Переинициализация для динамически добавленных элементов
    // (например, при переключении вкладок языков)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                initHelpIcons();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();