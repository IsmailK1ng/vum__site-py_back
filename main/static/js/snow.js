document.addEventListener("DOMContentLoaded", () => {
    let container = document.querySelector('.snow-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'snow-container';
        document.body.appendChild(container);
    }

    function getSnowSettings() {
        const width = window.innerWidth;
        
        if (width <= 480) {
            return { initialCount: 10, interval: 1500 };
        } else if (width <= 768) {
            return { initialCount: 20, interval: 1000 };
        } else if (width <= 1024) {
            return { initialCount: 30, interval: 700 };
        } else {
            return { initialCount: 50, interval: 500 };
        }
    }

    let settings = getSnowSettings();
    let snowInterval = null;

    // // Функция взрыва снежинки на частицы
    // function explodeSnowflake(flake, e) {
    //     const rect = flake.getBoundingClientRect();
    //     const x = rect.left + rect.width / 2;
    //     const y = rect.top + rect.height / 2;
    //     const size = parseFloat(flake.style.fontSize) || 1;
        
    //     // Удаляем оригинальную снежинку
    //     flake.remove();
        
    //     // Создаём осколки
    //     const particleCount = 8 + Math.floor(Math.random() * 5);
        
    //     for (let i = 0; i < particleCount; i++) {
    //         const particle = document.createElement('div');
    //         particle.className = 'snow-particle';
    //         particle.textContent = '❄';
            
    //         // Случайный угол и расстояние разлёта
    //         const angle = (Math.PI * 2 / particleCount) * i + Math.random() * 0.5;
    //         const velocity = 50 + Math.random() * 80;
    //         const destX = Math.cos(angle) * velocity;
    //         const destY = Math.sin(angle) * velocity;
    //         const rotation = Math.random() * 720 - 360;
            
    //         particle.style.cssText = `
    //             position: fixed;
    //             left: ${x}px;
    //             top: ${y}px;
    //             font-size: ${size * 0.4}em;
    //             color: #ffffff;
    //             text-shadow: 0 0 6px rgb(0, 136, 255), 0 0 12px rgb(0, 149, 255);
    //             pointer-events: none;
    //             z-index: 10000;
    //             opacity: 1;
    //             transform: translate(-50%, -50%);
    //             transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    //         `;
            
    //         document.body.appendChild(particle);
            
    //         // Запускаем анимацию разлёта
    //         requestAnimationFrame(() => {
    //             particle.style.transform = `translate(calc(-50% + ${destX}px), calc(-50% + ${destY}px)) rotate(${rotation}deg) scale(0.3)`;
    //             particle.style.opacity = '0';
    //         });
            
    //         // Удаляем частицу после анимации
    //         setTimeout(() => particle.remove(), 600);
    //     }
    // }

    function createSnowflake() {
        const currentSettings = getSnowSettings();
        const flake = document.createElement('div');
        flake.className = 'snowflake';
        flake.textContent = '❄';
        
        const size = Math.random() * 0.9 + 0.7;
        const duration = Math.random() * 20 + 15;
        const drift = (Math.random() * 100 - 50) + 'px';
        const rot = Math.random() * 720 + 'deg';
        const rotHalf = (parseFloat(rot)/2) + 'deg';
        
        flake.style.fontSize = size + 'em';
        flake.style.left = Math.random() * 100 + 'vw';
        flake.style.animationDuration = duration + 's';
        flake.style.setProperty('--drift', drift);
        flake.style.setProperty('--rot', rot);
        flake.style.setProperty('--rotHalf', rotHalf);

        // Клик — взрыв!
        flake.addEventListener('click', (e) => {
            e.stopPropagation();
            explodeSnowflake(flake, e);
        });

        container.appendChild(flake);
        setTimeout(() => flake.remove(), duration * 1000);
    }

    function startSnow() {
        settings = getSnowSettings();
        
        for (let i = 0; i < settings.initialCount; i++) {
            setTimeout(createSnowflake, i * 200);
        }
        
        if (snowInterval) clearInterval(snowInterval);
        snowInterval = setInterval(createSnowflake, settings.interval);
    }

    startSnow();

    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            const newSettings = getSnowSettings();
            if (newSettings.interval !== settings.interval) {
                if (snowInterval) clearInterval(snowInterval);
                settings = newSettings;
                snowInterval = setInterval(createSnowflake, settings.interval);
            }
        }, 250);
    });
});