document.addEventListener("DOMContentLoaded", () => {
    let container = document.querySelector('.snow-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'snow-container';
        document.body.appendChild(container);
    }

    function createSnowflake() {
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

        container.appendChild(flake);

        setTimeout(() => flake.remove(), duration * 1000);
    }

    for (let i = 0; i < 50; i++) setTimeout(createSnowflake, i*200);
    setInterval(createSnowflake, 500);
});
