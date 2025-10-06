/*!
 * FAW Trucks Website Scripts
 * Version: 1.1.0
 */

// --------------------------------------------- //
// FAW Stats Counters Initialization
// --------------------------------------------- //

document.addEventListener('DOMContentLoaded', function() {
  // FAW Stats initialization
  
  // Check if CountUp library is available
  if (typeof countUp === 'undefined') {
    console.error('CountUp library not found. Please ensure libs.min.js is loaded before this script.');
    return;
  }

  // Initialize counter animations with scroll spy
  initFAWCounters();
});

function initFAWCounters() {
  // Counter 1: 25+ Years Experience
  if (document.getElementById('stats-counter-1')) {
    const counter1 = new countUp.CountUp('stats-counter-1', 15, {
      suffix: '+',
      duration: 2.5,
      enableScrollSpy: true,
      scrollSpyOnce: true
    });
    
    if (!counter1.error) {
      console.log('Counter 1 initialized successfully');
    } else {
      console.error('Counter 1 error:', counter1.error);
    }
  }

  // Counter 2: 70+ Happy Customers  
  if (document.getElementById('stats-counter-2')) {
    const counter2 = new countUp.CountUp('stats-counter-2', 70, {
      suffix: '+',
      duration: 2.5,
      enableScrollSpy: true,
      scrollSpyOnce: true
    });
    
    if (!counter2.error) {
      console.log('Counter 2 initialized successfully');
    } else {
      console.error('Counter 2 error:', counter2.error);
    }
  }

  // Counter 3: 15+ Models
  if (document.getElementById('stats-counter-3')) {
    const counter3 = new countUp.CountUp('stats-counter-3', 15, {
      suffix: '+',
      duration: 2.5,
      enableScrollSpy: true,
      scrollSpyOnce: true
    });
    
    if (!counter3.error) {
      console.log('Counter 3 initialized successfully');
    } else {
      console.error('Counter 3 error:', counter3.error);
    }
  }

  // Counter 4: 24/7 Support (display as text immediately)
  if (document.getElementById('stats-counter-4')) {
    document.getElementById('stats-counter-4').textContent = '24/7';
    console.log('Counter 4 set to 24/7');
  }
}

// Alternative initialization method if CountUp doesn't support scrollSpy
function initCountersWithScrollObserver() {
  const counters = [
    { id: 'stats-counter-1', value: 25, suffix: '+' },
    { id: 'stats-counter-2', value: 500, suffix: '+' },
    { id: 'stats-counter-3', value: 15, suffix: '+' },
    { id: 'stats-counter-4', value: '24/7', isText: true }
  ];

  // Create intersection observer for scroll-triggered animation
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const counterId = entry.target.id;
        const counterData = counters.find(c => c.id === counterId);
        
        if (counterData) {
          if (counterData.isText) {
            entry.target.textContent = counterData.value;
          } else {
            const counter = new countUp.CountUp(counterId, counterData.value, {
              suffix: counterData.suffix || '',
              duration: 2.5
            });
            
            if (!counter.error) {
              counter.start();
            }
          }
          
          observer.unobserve(entry.target);
        }
      }
    });
  }, {
    threshold: 0.5,
    rootMargin: '0px 0px -50px 0px'
  });

  // Observe all counter elements
  counters.forEach(counterData => {
    const element = document.getElementById(counterData.id);
    if (element) {
      observer.observe(element);
    }
  });
}

// --------------------------------------------- //
// FAW Image Slider Functionality
// --------------------------------------------- //

// Данные слайдов
const slides = [
  {
    year: "2025",
    title: "FAW Tiger V 4x2",
    price: "434 000 000 sum",
    power: "185 o.k.",
    mpg: "17 L/100km",
    image: "/static/images/slider-foto_img/1.png",
    cta: [{ type: "main", label: "Batafsil", link: "#" }]
  },
  {
    year: "2025",
    title: "FAW Tiger V цельнометаллический",
    price: "419 104 000 sum",
    power: "185 o.k.",
    mpg: "17,1 L/100km",
    image: "/static/images/slider-foto_img/2.png",
    cta: [{ type: "main", label: "Batafsil", link: "#" }]
  },
  {
    year: "2025",
    title: "FAW Tiger V Pro",
    price: "480 000 000 sum",
    power: "195 o.k.",
    mpg: "16,8 L/100km",
    image: "/static/images/slider-foto_img/3.png",
    cta: [{ type: "main", label: "Batafsil", link: "#" }]
  }
];

// SVG-заглушка
function getPlaceholderSVG(title, size = "large") {
  let width = size === "large" ? 420 : 210;
  let height = size === "large" ? 210 : 105;
  let fsize = size === "large" ? 28 : 14;
  return `
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="${width}" height="${height}" rx="22" fill="#f8f8f8"/>
      <text x="50%" y="54%" text-anchor="middle" fill="#b4b4b4" font-size="${fsize}" font-family="Arial" dy=".3em">${title}</text>
    </svg>
  `;
}

let current = 0;
let animating = false;

// Получить индекс с циклическим переходом
function getIndex(idx) {
  return (idx + slides.length) % slides.length;
}

function setSlideContent(slideDiv, idx, pos) {
  const slide = slides[getIndex(idx)];
  slideDiv.innerHTML = slide.image
    ? `<img src="${slide.image}" alt="${slide.title}">`
    : getPlaceholderSVG(slide.title, pos === 'center' ? "large" : "small");
}

// Утилита: ждёт окончания CSS transition/animation на элементе с таймаутом-фоллбэком
function waitForTransition(element, fallback = 1000) {
  return new Promise((resolve, reject) => {
    if (!element) return reject(new Error('No element provided'));

    let finished = false;

    function onEnd(e) {
      if (e.target !== element) return;
      finished = true;
      element.removeEventListener('transitionend', onEnd);
      element.removeEventListener('animationend', onEnd);
      resolve();
    }

    element.addEventListener('transitionend', onEnd);
    element.addEventListener('animationend', onEnd);

    // Попытка вычислить длительность из CSS (transition + delay и animation + delay)
    try {
      const cs = window.getComputedStyle(element);
      const parseTimes = (str) => {
        if (!str) return [0];
        return str.split(',').map(s => parseFloat(s) || 0);
      };

      const tDur = parseTimes(cs.transitionDuration || '0s');
      const tDelay = parseTimes(cs.transitionDelay || '0s');
      const aDur = parseTimes(cs.animationDuration || '0s');
      const aDelay = parseTimes(cs.animationDelay || '0s');

      const toMs = (s) => {
        // если строка в секундах, parseFloat вернёт число; css может содержать '0.65s' но parseFloat даст 0.65
        return Math.round((s) * 1000);
      };

      // Найдём максимальную суммарную длительность
      const tMax = Math.max(...tDur.map((d, i) => toMs(d + (tDelay[i] || 0))));
      const aMax = Math.max(...aDur.map((d, i) => toMs(d + (aDelay[i] || 0))));
      const timeout = Math.max(tMax, aMax, fallback);

      // fallback таймаут
      setTimeout(() => {
        if (!finished) {
          element.removeEventListener('transitionend', onEnd);
          element.removeEventListener('animationend', onEnd);
          reject(new Error('transition timeout'));
        }
      }, timeout + 50); // небольшой запас
    } catch (err) {
      // если что-то пошло не так — используем fallback
      setTimeout(() => {
        if (!finished) {
          element.removeEventListener('transitionend', onEnd);
          element.removeEventListener('animationend', onEnd);
          reject(new Error('transition timeout'));
        }
      }, fallback);
    }
  });
}

// Главная функция анимации - как у FAW
function goTo(direction) {
  if (animating) return;
  animating = true;

  const leftDiv = document.getElementById('slide-left');
  const centerDiv = document.getElementById('slide-center');
  const rightDiv = document.getElementById('slide-right');
  const container = document.getElementById('slider-track');

  if (direction === 'right') {
    // Создаем новый правый слайд
    const newRight = document.createElement('div');
    newRight.className = 'faw-slide right';
    newRight.style.opacity = '0';
    setSlideContent(newRight, current + 2, 'right');
    container.appendChild(newRight);
    
    // Запускаем анимацию: используем requestAnimationFrame и форсированный reflow
    // чтобы гарантировать, что элемент вставлен в DOM и браузер применил
    // начальные стили (off-canvas), после чего добавление классов запустит transition.
    requestAnimationFrame(() => {
      // форсируем reflow
      /* eslint-disable no-unused-expressions */
      newRight.offsetHeight;
      /* eslint-enable no-unused-expressions */
      centerDiv.classList.add('moving-left');
      rightDiv.classList.add('moving-center');
      newRight.style.opacity = '0.65';
      newRight.classList.add('moving-right-in');
    });
    
    // Ждём окончания перехода вместо жёсткого таймаута
    waitForTransition(newRight, 1000).then(() => {
      current = getIndex(current + 1);

      // Удаляем старый левый
      leftDiv.remove();

      // Обновляем ID и классы
      centerDiv.id = 'slide-left';
      centerDiv.className = 'faw-slide left';

      rightDiv.id = 'slide-center';
      rightDiv.className = 'faw-slide center';

      newRight.id = 'slide-right';
      newRight.className = 'faw-slide right';
      newRight.style.opacity = '';

      animating = false;
      updateArrows();
      renderInfo(current);
    }).catch(() => {
      // fallback: если transitionend не сработал, всё равно завершаем через 700ms
      setTimeout(() => {
        current = getIndex(current + 1);
        leftDiv.remove();
        centerDiv.id = 'slide-left';
        centerDiv.className = 'faw-slide left';
        rightDiv.id = 'slide-center';
        rightDiv.className = 'faw-slide center';
        newRight.id = 'slide-right';
        newRight.className = 'faw-slide right';
        newRight.style.opacity = '';
        animating = false;
        updateArrows();
        renderInfo(current);
      }, 700);
    });
    
  } else if (direction === 'left') {
    // Создаем новый левый слайд
    const newLeft = document.createElement('div');
    newLeft.className = 'faw-slide left';
    newLeft.style.opacity = '0';
    setSlideContent(newLeft, current - 2, 'left');
    container.insertBefore(newLeft, leftDiv);
    
    // Запускаем анимацию: используем requestAnimationFrame и форсированный reflow
    requestAnimationFrame(() => {
      /* eslint-disable no-unused-expressions */
      newLeft.offsetHeight;
      /* eslint-enable no-unused-expressions */
      centerDiv.classList.add('moving-right');
      leftDiv.classList.add('moving-center');
      newLeft.style.opacity = '0.65';
      newLeft.classList.add('moving-left-in');
    });
    
    // Ждём окончания перехода вместо жёсткого таймаута
    waitForTransition(newLeft, 1000).then(() => {
      current = getIndex(current - 1);

      // Удаляем старый правый
      rightDiv.remove();

      // Обновляем ID и классы
      newLeft.id = 'slide-left';
      newLeft.className = 'faw-slide left';
      newLeft.style.opacity = '';

      leftDiv.id = 'slide-center';
      leftDiv.className = 'faw-slide center';

      centerDiv.id = 'slide-right';
      centerDiv.className = 'faw-slide right';

      animating = false;
      updateArrows();
      renderInfo(current);
    }).catch(() => {
      // fallback
      setTimeout(() => {
        current = getIndex(current - 1);
        rightDiv.remove();
        newLeft.id = 'slide-left';
        newLeft.className = 'faw-slide left';
        newLeft.style.opacity = '';
        leftDiv.id = 'slide-center';
        leftDiv.className = 'faw-slide center';
        centerDiv.id = 'slide-right';
        centerDiv.className = 'faw-slide right';
        animating = false;
        updateArrows();
        renderInfo(current);
      }, 700);
    });
  }
}

function renderInfo(idx) {
  const slide = slides[getIndex(idx)];
  let html = `<div class="faw-year">${slide.year}</div>
    <div class="faw-title">${slide.title}</div>
    <div class="faw-info-row">
      <div class="faw-info-col">
        <span class="faw-price-label">NARXI</span>
        <div class="faw-price-value">${slide.price}</div>
      </div>
      <div class="faw-info-col">
        <span class="faw-power-label">KUCH</span>
        <div class="faw-power-value">${slide.power}</div>
      </div>
      <div class="faw-info-col">
        <span class="faw-mpg-label">RASHOD</span>
        <div class="faw-mpg-value">${slide.mpg}</div>
      </div>
    </div>
    <div class="faw-slider-buttons">
      ${slide.cta.map(btn => `<a href="${btn.link}" class="faw-btn">${btn.label}</a>`).join('')}
    </div>
  `;
  document.getElementById('slider-info').innerHTML = html;
}

function updateArrows() {
  const leftArrow = document.querySelector('.faw-slider-arrow.left');
  const rightArrow = document.querySelector('.faw-slider-arrow.right');
  if (leftArrow) leftArrow.disabled = animating;
  if (rightArrow) rightArrow.disabled = animating;
}

// Инициализация слайдера при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
  
  // Проверяем наличие элементов слайдера
  const sliderTrack = document.getElementById('slider-track');
  const sliderInfo = document.getElementById('slider-info');
  const slideLeft = document.getElementById('slide-left');
  const slideCenter = document.getElementById('slide-center');
  const slideRight = document.getElementById('slide-right');
  
  if (sliderTrack && sliderInfo && slideLeft && slideCenter && slideRight) {
    
    // Навешиваем обработчики
    const leftArrow = document.querySelector('.faw-slider-arrow.left-btn');
    const rightArrow = document.querySelector('.faw-slider-arrow.right-btn');

    if (leftArrow) {
      leftArrow.setAttribute('type', 'button');
      leftArrow.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (!animating) goTo('left');
      });
    }
    if (rightArrow) {
      rightArrow.setAttribute('type', 'button');
      rightArrow.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (!animating) goTo('right');
      });
    }

    // Инициализация слайдера
    setSlideContent(slideLeft, current - 1, 'left');
    setSlideContent(slideCenter, current, 'center');
    setSlideContent(slideRight, current + 1, 'right');
    renderInfo(current);
    updateArrows();
    // --- Autoplay setup: start/stop/reset ---
    let autoPlayDelay = 5000; // ms
    let autoPlayTimer = null;

    function isSmallScreen() {
      return window.innerWidth < 450;
    }

    function startAutoplay() {
      // don't start on very small screens
      if (isSmallScreen()) return;
      if (autoPlayTimer) return;
      autoPlayTimer = setInterval(() => {
        if (!animating) goTo('right');
      }, autoPlayDelay);
    }

    function stopAutoplay() {
      if (autoPlayTimer) {
        clearInterval(autoPlayTimer);
        autoPlayTimer = null;
      }
    }

    function resetAutoplay() {
      stopAutoplay();
      // small delay before restart to avoid immediate jump after manual action
      setTimeout(() => startAutoplay(), 600);
    }

    // start autoplay by default only if not small screen
    if (!isSmallScreen()) startAutoplay();

    // Pause on hover / touch
    // Use the already-declared `sliderTrack` variable here — `sliderTrackEl` is declared later
    // and referencing it earlier caused a ReferenceError (TDZ) which aborted execution
    if (sliderTrack) {
      sliderTrack.addEventListener('mouseenter', stopAutoplay, { passive: true });
      sliderTrack.addEventListener('mouseleave', () => { if (!isSmallScreen()) startAutoplay(); }, { passive: true });
      sliderTrack.addEventListener('touchstart', stopAutoplay, { passive: true });
      sliderTrack.addEventListener('touchend', () => setTimeout(() => { if (!isSmallScreen()) startAutoplay(); }, 800), { passive: true });
    }

    // Pause when page is hidden, resume when visible (respect small screen)
    document.addEventListener('visibilitychange', function() {
      if (document.hidden) stopAutoplay(); else { if (!isSmallScreen()) startAutoplay(); }
    });

    // Toggle autoplay when crossing 450px threshold
    let lastSmall = isSmallScreen();
    window.addEventListener('resize', function() {
      const nowSmall = isSmallScreen();
      if (nowSmall && !lastSmall) {
        // just became small -> stop autoplay
        stopAutoplay();
      } else if (!nowSmall && lastSmall) {
        // just became large enough -> start autoplay
        startAutoplay();
      }
      lastSmall = nowSmall;
    });

    // Делегированный обработчик кликов: работает даже если крайние слайды пересоздаются
    const sliderTrackEl = document.getElementById('slider-track');
    if (sliderTrackEl) {
      sliderTrackEl.addEventListener('click', function(ev) {
        const slideEl = ev.target.closest('.faw-slide');
        if (!slideEl) return;
        // Игнорируем клик по центральному слайду
        if (slideEl.id === 'slide-left' && !animating) {
          goTo('left');
        } else if (slideEl.id === 'slide-right' && !animating) {
          goTo('right');
        }
      });
    }
    // Клавиатурная навигация (стрелки) — только если фокус не в поле ввода
    document.addEventListener('keydown', function(e) {
      const active = document.activeElement;
      const tag = active && active.tagName && active.tagName.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || active && active.isContentEditable) return;
      if (e.key === 'ArrowLeft') {
        if (!animating) goTo('left');
      } else if (e.key === 'ArrowRight') {
        if (!animating) goTo('right');
      }
    });

    // Простая поддержка свайпа для мобильных устройств
    (function addSwipeSupport() {
      let touchStartX = 0;
      let touchStartY = 0;
      let touchMoved = false;
      const threshold = 50; // px

      sliderTrackEl.addEventListener('touchstart', function(ev) {
        if (!ev.touches || ev.touches.length > 1) return;
        touchMoved = false;
        touchStartX = ev.touches[0].clientX;
        touchStartY = ev.touches[0].clientY;
      }, { passive: true });

      sliderTrackEl.addEventListener('touchmove', function(ev) {
        if (!ev.touches || ev.touches.length > 1) return;
        const dx = ev.touches[0].clientX - touchStartX;
        const dy = ev.touches[0].clientY - touchStartY;
        // Если вертикальное движение больше горизонтального — игнорируем (скролл)
        if (Math.abs(dy) > Math.abs(dx)) return;
        if (Math.abs(dx) > 10) touchMoved = true;
      }, { passive: true });

      sliderTrackEl.addEventListener('touchend', function(ev) {
        if (!touchMoved) return;
        const lastTouch = ev.changedTouches && ev.changedTouches[0];
        if (!lastTouch) return;
        const dx = lastTouch.clientX - touchStartX;
        if (Math.abs(dx) < threshold) return;
        if (dx < 0) {
          // свайп влево — следующий слайд
          if (!animating) goTo('right');
        } else {
          // свайп вправо — предыдущий слайд
          if (!animating) goTo('left');
        }
      }, { passive: true });
      // swipe support added
    })();
  } else {
    console.error('FAW Slider elements not found. Check HTML structure.');
  }
});

// --------------------------------------------- //
// Fixed Header with Scroll Effect - Run immediately
// --------------------------------------------- //

(function() {
  const header = document.getElementById('header');
  let scrollTimeout;

  function getTheme() {
    // Check localStorage first
    const savedTheme = localStorage.getItem('color-theme');
    if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
      return savedTheme;
    }
    
    // Check manual theme setting
    if (document.body.dataset.theme) {
      return document.body.dataset.theme;
    }
    
    // Check color-scheme attribute
    if (document.documentElement.getAttribute('color-scheme')) {
      return document.documentElement.getAttribute('color-scheme');
    }
    
    // По умолчанию всегда светлая тема (игнорируем системные настройки)
    return 'light';
  }

  function setTheme(theme) {
    // Save to localStorage
    localStorage.setItem('color-theme', theme);
    
    // Set attributes
    document.documentElement.setAttribute('color-scheme', theme);
    document.body.setAttribute('data-theme', theme);
    
    // Add CSS classes for better control
    if (theme === 'dark') {
      document.body.classList.add('dark-mode');
      document.body.classList.remove('light-mode');
    } else {
      document.body.classList.add('light-mode');
      document.body.classList.remove('dark-mode');
    }
  }

  function isMobile() {
    return window.innerWidth < 1200;
  }

  function updateHeaderTheme() {
    if (!header) return;
    
    const theme = getTheme();
    const mobile = isMobile();
    
    // Remove any old theme classes
    header.classList.remove('light-theme', 'dark-theme');
    
    // On mobile - keep transparent
    if (mobile) {
      header.style.background = 'transparent';
      header.style.backgroundColor = 'transparent';
      header.style.boxShadow = 'none';
      header.style.border = 'none';
      header.style.backdropFilter = 'none';
      header.style.webkitBackdropFilter = 'none';
      
      // Add theme class without forcing colors
      if (theme === 'dark') {
        header.classList.add('dark-theme');
      } else {
        header.classList.add('light-theme');
      }
      return;
    }
    
    // Desktop - add theme class and let CSS handle styling
    if (theme === 'dark') {
      header.classList.add('dark-theme');
    } else {
      header.classList.add('light-theme');
    }
    
    // Ensure Z-index is correct
    header.style.zIndex = '9999';
  }

  function initHeader() {
    if (header) {
      // Initialize theme from localStorage
      const savedTheme = getTheme();
      setTheme(savedTheme);
      console.log('Theme initialized from localStorage:', savedTheme);
      
      // Remove any existing problematic classes
      header.classList.remove('transparent', 'mxd-header');
      
      // Set initial state - solid
      header.classList.add('solid');
      
      console.log('Header found and initialized with adaptive theme');

      // Initial theme setup
      updateHeaderTheme();

      // Throttled scroll handler
      function handleScroll() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          const scrollY = window.scrollY;
          
          if (scrollY > 10) {
            header.classList.add('scrolled');
          } else {
            header.classList.remove('scrolled');
          }
          
          // Update theme-specific styles
          updateHeaderTheme();
        }, 3);
      }

      // Add scroll listener
      window.addEventListener('scroll', handleScroll);
      
      // Add resize listener to handle mobile/desktop switch
      window.addEventListener('resize', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(updateHeaderTheme, 100);
      });
      
      // Listen for theme changes
      if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateHeaderTheme);
      }
      
      // Listen for manual theme changes
      const observer = new MutationObserver(updateHeaderTheme);
      observer.observe(document.body, { attributes: true, attributeFilter: ['data-theme', 'class'] });
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ['color-scheme'] });
      
      // Add theme switcher functionality
      const colorSwitcher = document.getElementById('color-switcher');
      if (colorSwitcher) {
        colorSwitcher.addEventListener('click', function() {
          const currentTheme = getTheme();
          const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
          
          // Set new theme using our function
          setTheme(newTheme);
          
          // Update header immediately
          setTimeout(updateHeaderTheme, 50);
          
          console.log('Theme switched to:', newTheme);
        });
        console.log('Theme switcher button found and connected');
      }
      
      console.log('Fixed header scroll listener, resize listener and theme observer added');
    } else {
      console.log('Header not found yet, will retry...');
      setTimeout(initHeader, 100);
    }
  }

  // Start immediately
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeader);
  } else {
    initHeader();
  }
})();

// --------------------------------------------- //
// FAW Contact Form Handler
// --------------------------------------------- //

(function() {
  'use strict';

  // Show loading state
  function showLoadingState(button, loading = true) {
    if (!button) {
      console.error('Button not found in showLoadingState');
      return;
    }
    
    // Ensure form remains visible
    const form = button.closest('form');
    if (form) {
      form.style.visibility = 'visible';
      form.style.display = 'block';
      form.style.opacity = '1';
      
      // Also ensure parent containers remain visible
      const container = form.closest('.form-container');
      if (container) {
        container.style.visibility = 'visible';
        container.style.display = 'block';
        container.style.opacity = '1';
      }
    }
    
    const textElement = button.querySelector('.t-btnflex__text');
    if (!textElement) {
      console.error('Text element not found in button');
      return;
    }
    
    if (loading) {
      button.disabled = true;
      button.classList.add('loading');
      button.style.opacity = '0.8';
      textElement.textContent = 'Yuborilmoqda...';
      console.log('Button set to loading state');
    } else {
      button.disabled = false;
      button.classList.remove('loading');
      button.style.opacity = '1';
      console.log('Button loading state removed');
    }
  }

  // Show field error
  function showFieldError(field, message) {
    field.classList.add('error');
    
    // For phone mask wrapper
    const phoneWrapper = field.closest('.t-input-phonemask__wrap');
    if (phoneWrapper) {
      phoneWrapper.classList.add('error');
    }
    
    // Show full error messages
    const errorElement = field.closest('.t-input-group').querySelector('.t-input-error');
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.add('show');
    }
    field.style.borderColor = '#e74c3c';
  }

  // Hide field error
  function hideFieldError(field) {
    field.classList.remove('error');
    
    // For phone mask wrapper
    const phoneWrapper = field.closest('.t-input-phonemask__wrap');
    if (phoneWrapper) {
      phoneWrapper.classList.remove('error');
    }
    
    // Hide error messages
    const errorElement = field.closest('.t-input-group').querySelector('.t-input-error');
    if (errorElement) {
      errorElement.textContent = '';
      errorElement.classList.remove('show');
    }
    field.style.borderColor = '';
  }

  // Submit form data
  function submitFormData(formData) {
    // Here you would typically send the data to your server
    // For now, we'll just log it and show a success message
    
    console.log('Form data to submit:', {
      name: formData.get('Name'),
      region: formData.get('REGION'),
      phone: formData.get('Phone'),
      message: formData.get('Textarea')
    });
    
    // Simulate API call
    return new Promise((resolve) => {
      setTimeout(() => {
        // Simulate 90% success rate
        const success = Math.random() > 0.1;
        resolve({ success });
      }, 1500);
    });
  }

  // Initialize contact form
  function initContactForm() {
    const mainForm = document.getElementById('faw-main-contact-form');
    
    if (mainForm) {
      console.log('FAW Main Contact Form found, initializing...');
      setupForm(mainForm, 'main_input_', 'main_error_');
    } else {
      console.warn('FAW Main Contact Form not found');
    }
  }

  // Setup form functionality
  function setupForm(form, inputPrefix, errorPrefix) {
    // Initialize phone mask
    initPhoneMaskForForm(form, inputPrefix);
    
    // Handle form submission
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log('Form submission started for:', this.id);
      
      const submitButton = this.querySelector('.t-btnflex');
      if (!submitButton) {
        console.error('Submit button not found');
        return;
      }
      
      const originalText = submitButton.querySelector('.t-btnflex__text').textContent;
      
      try {
        // Validate form
        const errors = validateFormData(this, inputPrefix, errorPrefix);
        showFormErrors(errors, this);
        
        if (errors.length > 0) {
          console.log('Validation errors found:', errors);
          // Only scroll to error for main form, not footer form
          if (this.id === 'faw-main-contact-form') {
            const firstError = this.querySelector('.t-input-error.show');
            if (firstError) {
              firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          }
          // Reset button state if there are validation errors
          submitButton.disabled = false;
          submitButton.classList.remove('loading');
          return;
        }
        
        // Show loading state
        showLoadingState(submitButton, true);
        console.log('Form validation passed, submitting...');
        
        // Get form data
        const formData = new FormData(this);
        
        // Submit form
        const result = await submitFormData(formData);
        
        if (result.success) {
          console.log('Form submitted successfully');
          showSuccessMessage(this, submitButton, originalText);
          showFormErrors([], this); // Clear any errors
        } else {
          throw new Error('Yuborishda xatolik yuz berdi');
        }
      } catch (error) {
        console.error('Form submission error:', error);
        showFormErrors(['Yuborishda xatolik yuz berdi. Iltimos, qayta urinib ko\'ring.'], this);
        
        showLoadingState(submitButton, false);
        submitButton.querySelector('.t-btnflex__text').textContent = originalText;
      }
    });
    
    // Clear errors on input
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      input.addEventListener('input', function() {
        hideFieldError(this);
      });
    });
    
    console.log('FAW Contact Form initialized successfully');
  }

  // Phone mask setup for specific form
  function initPhoneMaskForForm(form, inputPrefix) {
    const phoneInput = form.querySelector('#' + inputPrefix + '1496238250184');
    if (phoneInput) {
      // Simple phone mask for Uzbekistan format
      phoneInput.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        
        // Limit to 9 digits (without country code)
        if (value.length > 9) {
          value = value.substring(0, 9);
        }
        
        // Format as XX-XXX-XXXX
        if (value.length >= 2) {
          value = value.substring(0, 2) + '-' + value.substring(2);
        }
        if (value.length >= 6) {
          value = value.substring(0, 6) + '-' + value.substring(6);
        }
        
        e.target.value = value;
        
        // Update hidden field for form submission
        const hiddenPhone = form.querySelector('input[name="Phone"]');
        if (hiddenPhone) {
          hiddenPhone.value = '+998-' + value;
        }
      });
      
      phoneInput.addEventListener('focus', function() {
        if (!this.value) {
          this.placeholder = 'XX-XXX-XXXX';
        }
      });
      
      phoneInput.addEventListener('blur', function() {
        if (!this.value) {
          this.placeholder = '99-999-9999';
        }
      });
    }
  }

  // Form validation for specific form
  function validateFormData(form, inputPrefix, errorPrefix) {
    const errors = [];
    
    // Name validation
    const nameInput = form.querySelector('#' + inputPrefix + '1496238230199');
    if (!nameInput.value.trim()) {
      errors.push('Ism kiritish majburiy');
      showFieldError(nameInput, 'Bu maydon to\'ldirilishi shart');
    } else if (nameInput.value.trim().length < 2) {
      errors.push('Ism kamida 2 ta belgidan iborat bo\'lishi kerak');
      showFieldError(nameInput, 'Kamida 2 ta belgi kiriting');
    } else {
      hideFieldError(nameInput);
    }
    
    // Region validation
    const regionSelect = form.querySelector('#' + inputPrefix + '1674719958962');
    if (!regionSelect.value) {
      errors.push('Viloyat tanlanishi majburiy');
      showFieldError(regionSelect, 'Viloyatni tanlang');
    } else {
      hideFieldError(regionSelect);
    }
    
    // Phone validation
    const phoneInput = form.querySelector('#' + inputPrefix + '1496238250184');
    const phoneValue = phoneInput.value.replace(/\D/g, '');
    if (!phoneValue || phoneValue.length !== 9) {
      errors.push('To\'g\'ri telefon raqam kiriting');
      showFieldError(phoneInput, 'To\'g\'ri telefon raqam kiriting (9 raqam)');
    } else {
      hideFieldError(phoneInput);
    }
    
    return errors;
  }

  // Show general form errors for specific form
  function showFormErrors(errors, form) {
    const errorBox = form.querySelector('.js-errorbox-all');
    const errorList = errorBox.querySelector('.t-form__errorbox-text');
    
    if (errors.length > 0) {
      errorList.innerHTML = '';
      errors.forEach(error => {
        const li = document.createElement('li');
        li.className = 't-form__errorbox-item';
        li.textContent = error;
        errorList.appendChild(li);
      });
      errorBox.style.display = 'block';
    } else {
      errorBox.style.display = 'none';
    }
  }

  // Show success message for specific form
  function showSuccessMessage(form, submitButton, originalText) {
    if (!form || !submitButton) {
      console.error('Form or button not found in showSuccessMessage');
      return;
    }
    
    console.log('Showing success message for form:', form.id);
    
    // Ensure form remains visible during success state
    form.style.visibility = 'visible';
    form.style.display = 'block';
    form.style.opacity = '1';
    
    // Also ensure parent containers remain visible
    const container = form.closest('.form-container');
    if (container) {
      container.style.visibility = 'visible';
      container.style.display = 'block';
      container.style.opacity = '1';
    }
    
    const textElement = submitButton.querySelector('.t-btnflex__text');
    if (!textElement) {
      console.error('Text element not found in success message');
      return;
    }
    
    submitButton.classList.add('success');
    submitButton.style.opacity = '1';
    textElement.textContent = 'Yuborildi!';
    
    setTimeout(() => {
      if (submitButton && textElement) {
        submitButton.classList.remove('success');
        submitButton.disabled = false;
        textElement.textContent = originalText;
        
        // Reset form only if it still exists
        if (form && form.reset) {
          form.reset();
          console.log('Form reset completed');
        }
        
        // Reset phone mask
        const phoneInput = form.querySelector('input[type="tel"]');
        if (phoneInput) {
          phoneInput.placeholder = '99-999-9999';
          phoneInput.value = '';
        }
        
        // Clear all error states
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
          input.classList.remove('error');
        });
        
        const phoneWrappers = form.querySelectorAll('.t-input-phonemask__wrap');
        phoneWrappers.forEach(wrapper => {
          wrapper.classList.remove('error');
        });
      }
    }, 3000);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initContactForm);
  } else {
    initContactForm();
  }
})();

// --------------------------------------------- //
// FAW Trucks Model Cards Pagination
// --------------------------------------------- //


