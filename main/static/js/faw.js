/*!
 * FAW Trucks Website Scripts
 * Version: 1.2.0 - Optimized
 */

// --------------------------------------------- //
// FAW Stats Counters Initialization
// --------------------------------------------- //

document.addEventListener('DOMContentLoaded', function () {
  if (typeof countUp === 'undefined') {
    window.logJSError('CountUp library not found', { file: 'faw-scripts.js' });
    return;
  }
  initFAWCounters();
});

function initFAWCounters() {
  const counters = [
    { id: 'stats-counter-1', value: 15, suffix: '+' },
    { id: 'stats-counter-2', value: 70, suffix: '+' },
    { id: 'stats-counter-3', value: 15, suffix: '+' },
    { id: 'stats-counter-4', value: '24/7', isText: true }
  ];

  counters.forEach(counterData => {
    const element = document.getElementById(counterData.id);
    if (!element) return;

    if (counterData.isText) {
      element.textContent = counterData.value;
    } else {
      const counter = new countUp.CountUp(counterData.id, counterData.value, {
        suffix: counterData.suffix,
        duration: 2.5,
        enableScrollSpy: true,
        scrollSpyOnce: true
      });
    }
  });
}

// --------------------------------------------- //
// FAW Image Slider Functionality
// --------------------------------------------- //

// Slides are loaded dynamically from Django (via a DOM element with id="slider-data").
// If no data is provided, a fallback static list will be used.
let slides = [];

function initializeSlidesFromDjango() {

  const sliderDataElement = document.getElementById('slider-data');

  if (!sliderDataElement) {
    loadFallbackSlides();
    return false;
  }


  // Получаем содержимое в зависимости от типа элемента
  let content = '';

  if (sliderDataElement.tagName === 'SCRIPT') {
    // Если это <script type="application/json">
    content = sliderDataElement.textContent || sliderDataElement.innerHTML;
  } else {
    // Если это <div> или другой элемент
    content = sliderDataElement.textContent;
  }

  // Убираем лишние пробелы и переносы строк
  content = content.trim();


  if (!content) {
    loadFallbackSlides();
    return false;
  }

  try {
    const djangoSlides = JSON.parse(content);

    if (!Array.isArray(djangoSlides)) {
      loadFallbackSlides();
      return false;
    }

    if (djangoSlides.length === 0) {
      loadFallbackSlides();
      return false;
    }

    slides = djangoSlides.map(slide => ({
      year: slide.year || "2025",
      title: slide.title || "FAW Truck",
      price: slide.price || "Narx so'rang",
      power: slide.power || "—",
      mpg: slide.mpg || "—",
      image: slide.image || null,
      cta: [{ type: "main", label: "Batafsil", link: slide.link || "#" }]
    }));

    return true;

  } catch (error) {
    loadFallbackSlides();
    return false;
  }
}

function loadFallbackSlides() {


  slides = [
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
}
function getPlaceholderSVG(title, size = "large") {
  const dimensions = size === "large" ? { w: 420, h: 210, fs: 28 } : { w: 210, h: 105, fs: 14 };
  return `<svg width="${dimensions.w}" height="${dimensions.h}" viewBox="0 0 ${dimensions.w} ${dimensions.h}" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="${dimensions.w}" height="${dimensions.h}" rx="22" fill="#f8f8f8"/>
    <text x="50%" y="54%" text-anchor="middle" fill="#b4b4b4" font-size="${dimensions.fs}" font-family="Arial" dy=".3em">${title}</text>
  </svg>`;
}

let current = 0;
let animating = false;

function getIndex(idx) {
  return (idx + slides.length) % slides.length;
}

function setSlideContent(slideDiv, idx, pos) {
  const slide = slides[getIndex(idx)];
  slideDiv.innerHTML = slide.image
    ? `<img src="${slide.image}" alt="${slide.title}">`
    : getPlaceholderSVG(slide.title, pos === 'center' ? "large" : "small");
}

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

    try {
      const cs = window.getComputedStyle(element);
      const parseTimes = (str) => str ? str.split(',').map(s => parseFloat(s) || 0) : [0];
      const toMs = (s) => Math.round(s * 1000);

      const tDur = parseTimes(cs.transitionDuration || '0s');
      const tDelay = parseTimes(cs.transitionDelay || '0s');
      const aDur = parseTimes(cs.animationDuration || '0s');
      const aDelay = parseTimes(cs.animationDelay || '0s');

      const tMax = Math.max(...tDur.map((d, i) => toMs(d + (tDelay[i] || 0))));
      const aMax = Math.max(...aDur.map((d, i) => toMs(d + (aDelay[i] || 0))));
      const timeout = Math.max(tMax, aMax, fallback);

      setTimeout(() => {
        if (!finished) {
          element.removeEventListener('transitionend', onEnd);
          element.removeEventListener('animationend', onEnd);
          reject(new Error('transition timeout'));
        }
      }, timeout + 50);
    } catch (err) {
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

function goTo(direction) {
  if (animating) return;
  animating = true;

  const leftDiv = document.getElementById('slide-left');
  const centerDiv = document.getElementById('slide-center');
  const rightDiv = document.getElementById('slide-right');
  const container = document.getElementById('slider-track');

  if (direction === 'right') {
    const newRight = document.createElement('div');
    newRight.className = 'faw-slide right';
    newRight.style.opacity = '0';
    setSlideContent(newRight, current + 2, 'right');
    container.appendChild(newRight);

    requestAnimationFrame(() => {
      newRight.offsetHeight;
      centerDiv.classList.add('moving-left');
      rightDiv.classList.add('moving-center');
      newRight.style.opacity = '0.65';
      newRight.classList.add('moving-right-in');
    });

    waitForTransition(newRight, 1000).then(() => {
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
    }).catch(() => {
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
    const newLeft = document.createElement('div');
    newLeft.className = 'faw-slide left';
    newLeft.style.opacity = '0';
    setSlideContent(newLeft, current - 2, 'left');
    container.insertBefore(newLeft, leftDiv);

    requestAnimationFrame(() => {
      newLeft.offsetHeight;
      centerDiv.classList.add('moving-right');
      leftDiv.classList.add('moving-center');
      newLeft.style.opacity = '0.65';
      newLeft.classList.add('moving-left-in');
    });

    waitForTransition(newLeft, 1000).then(() => {
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
    }).catch(() => {
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
  document.getElementById('slider-info').innerHTML = `
    <div class="faw-year">${slide.year}</div>
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
}

function updateArrows() {
  const arrows = document.querySelectorAll('.faw-slider-arrow');
  arrows.forEach(arrow => arrow.disabled = animating);
}

document.addEventListener('DOMContentLoaded', function () {
  // Попытка загрузить слайды из Django (<div id="slider-data">[...]</div>)
  initializeSlidesFromDjango();

  if (!slides || slides.length === 0) {
    console.error('❌ No slides available for slider');
    return;
  }

  const sliderTrack = document.getElementById('slider-track');
  const sliderInfo = document.getElementById('slider-info');
  const slideLeft = document.getElementById('slide-left');
  const slideCenter = document.getElementById('slide-center');
  const slideRight = document.getElementById('slide-right');

  if (sliderTrack && sliderInfo && slideLeft && slideCenter && slideRight) {
    const leftArrow = document.querySelector('.faw-slider-arrow.left-btn');
    const rightArrow = document.querySelector('.faw-slider-arrow.right-btn');

    if (leftArrow) {
      leftArrow.setAttribute('type', 'button');
      leftArrow.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (!animating) goTo('left');
      });
    }
    if (rightArrow) {
      rightArrow.setAttribute('type', 'button');
      rightArrow.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (!animating) goTo('right');
      });
    }

    setSlideContent(slideLeft, current - 1, 'left');
    setSlideContent(slideCenter, current, 'center');
    setSlideContent(slideRight, current + 1, 'right');
    renderInfo(current);
    updateArrows();

    let autoPlayDelay = 5000;
    let autoPlayTimer = null;

    const isSmallScreen = () => window.innerWidth < 450;

    function startAutoplay() {
      if (isSmallScreen() || autoPlayTimer) return;
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

    if (!isSmallScreen()) startAutoplay();

    if (sliderTrack) {
      sliderTrack.addEventListener('mouseenter', stopAutoplay, { passive: true });
      sliderTrack.addEventListener('mouseleave', () => { if (!isSmallScreen()) startAutoplay(); }, { passive: true });
      sliderTrack.addEventListener('touchstart', stopAutoplay, { passive: true });
      sliderTrack.addEventListener('touchend', () => setTimeout(() => { if (!isSmallScreen()) startAutoplay(); }, 800), { passive: true });
    }

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stopAutoplay();
      else if (!isSmallScreen()) startAutoplay();
    });

    let lastSmall = isSmallScreen();
    window.addEventListener('resize', function () {
      const nowSmall = isSmallScreen();
      if (nowSmall && !lastSmall) {
        stopAutoplay();
      } else if (!nowSmall && lastSmall) {
        startAutoplay();
      }
      lastSmall = nowSmall;
    });

    const sliderTrackEl = document.getElementById('slider-track');
    if (sliderTrackEl) {
      sliderTrackEl.addEventListener('click', function (ev) {
        const slideEl = ev.target.closest('.faw-slide');
        if (!slideEl || animating) return;
        if (slideEl.id === 'slide-left') goTo('left');
        else if (slideEl.id === 'slide-right') goTo('right');
      });
    }

    document.addEventListener('keydown', function (e) {
      const active = document.activeElement;
      const tag = active?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || active?.isContentEditable) return;
      if (e.key === 'ArrowLeft' && !animating) goTo('left');
      else if (e.key === 'ArrowRight' && !animating) goTo('right');
    });

    (function addSwipeSupport() {
      let touchStartX = 0;
      let touchStartY = 0;
      let touchMoved = false;
      const threshold = 50;

      sliderTrackEl.addEventListener('touchstart', function (ev) {
        if (!ev.touches || ev.touches.length > 1) return;
        touchMoved = false;
        touchStartX = ev.touches[0].clientX;
        touchStartY = ev.touches[0].clientY;
      }, { passive: true });

      sliderTrackEl.addEventListener('touchmove', function (ev) {
        if (!ev.touches || ev.touches.length > 1) return;
        const dx = ev.touches[0].clientX - touchStartX;
        const dy = ev.touches[0].clientY - touchStartY;
        if (Math.abs(dy) > Math.abs(dx)) return;
        if (Math.abs(dx) > 10) touchMoved = true;
      }, { passive: true });

      sliderTrackEl.addEventListener('touchend', function (ev) {
        if (!touchMoved) return;
        const lastTouch = ev.changedTouches?.[0];
        if (!lastTouch) return;
        const dx = lastTouch.clientX - touchStartX;
        if (Math.abs(dx) < threshold) return;
        if (dx < 0 && !animating) goTo('right');
        else if (dx > 0 && !animating) goTo('left');
      }, { passive: true });
    })();
  } else {
  }
});

// --------------------------------------------- //
// Fixed Header with Scroll Effect
// --------------------------------------------- //

(function () {
  const header = document.getElementById('header');
  let scrollTimeout;

  function getTheme() {
    const savedTheme = localStorage.getItem('color-theme');
    if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) return savedTheme;
    if (document.body.dataset.theme) return document.body.dataset.theme;
    if (document.documentElement.getAttribute('color-scheme')) {
      return document.documentElement.getAttribute('color-scheme');
    }
    return 'light';
  }

  function setTheme(theme) {
    localStorage.setItem('color-theme', theme);
    document.documentElement.setAttribute('color-scheme', theme);
    document.body.setAttribute('data-theme', theme);

    if (theme === 'dark') {
      document.body.classList.add('dark-mode');
      document.body.classList.remove('light-mode');
    } else {
      document.body.classList.add('light-mode');
      document.body.classList.remove('dark-mode');
    }
  }

  const isMobile = () => window.innerWidth < 1200;

  function updateHeaderTheme() {
    if (!header) return;

    const theme = getTheme();
    const mobile = isMobile();

    header.classList.remove('light-theme', 'dark-theme');

    if (mobile) {
      Object.assign(header.style, {
        background: 'transparent',
        backgroundColor: 'transparent',
        boxShadow: 'none',
        border: 'none',
        backdropFilter: 'none',
        webkitBackdropFilter: 'none'
      });
      header.classList.add(theme === 'dark' ? 'dark-theme' : 'light-theme');
      return;
    }

    header.classList.add(theme === 'dark' ? 'dark-theme' : 'light-theme');
    header.style.zIndex = '9999';
  }

  function initHeader() {
    if (header) {
      const savedTheme = getTheme();
      setTheme(savedTheme);

      header.classList.remove('transparent', 'mxd-header');
      header.classList.add('solid');


      updateHeaderTheme();

      function handleScroll() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          header.classList.toggle('scrolled', window.scrollY > 10);
          updateHeaderTheme();
        }, 3);
      }

      window.addEventListener('scroll', handleScroll);
      window.addEventListener('resize', function () {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(updateHeaderTheme, 100);
      });

      if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateHeaderTheme);
      }

      const observer = new MutationObserver(updateHeaderTheme);
      observer.observe(document.body, { attributes: true, attributeFilter: ['data-theme', 'class'] });
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ['color-scheme'] });

      const colorSwitcher = document.getElementById('color-switcher');
      if (colorSwitcher) {
        colorSwitcher.addEventListener('click', function () {
          const currentTheme = getTheme();
          const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
          setTheme(newTheme);
          setTimeout(updateHeaderTheme, 50);
        });
      }

    } else {
      setTimeout(initHeader, 100);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeader);
  } else {
    initHeader();
  }
})();

// --------------------------------------------- //
// Universal Phone Mask for All Forms (Uzbekistan: +998 + 9 digits)
// --------------------------------------------- //
(function () {
  'use strict';

  function formatPhone(numbers) {
    const userPart = numbers.substring(3);
    let formatted = '+998';

    if (userPart.length > 0) {
      formatted += ' (' + userPart.substring(0, 2);
      if (userPart.length > 2) {
        formatted += ') ' + userPart.substring(2, 5);
        if (userPart.length > 5) {
          formatted += '-' + userPart.substring(5, 7);
          if (userPart.length > 7) {
            formatted += '-' + userPart.substring(7, 9);
          }
        }
      } else if (userPart.length === 2) {
        formatted += ')';
      }
    } else {
      formatted += ' ';
    }

    return formatted;
  }

  function initPhoneMask(phoneInput) {
    // Проверяем, не инициализирован ли уже
    if (phoneInput.dataset.phoneMaskInitialized) return;
    phoneInput.dataset.phoneMaskInitialized = 'true';

    phoneInput.placeholder = '+998 (__) ___-__-__';
    if (!phoneInput.value || phoneInput.value === '') {
      phoneInput.value = '+998 ';
    }

    phoneInput.addEventListener('input', function (e) {
      let value = e.target.value;
      let numbers = value.replace(/\D/g, '');

      if (!value.startsWith('+998')) {
        value = '+998 ';
        numbers = '998';
      }

      if (numbers.length > 12) {
        numbers = numbers.substring(0, 12);
      }

      e.target.value = formatPhone(numbers);
    });

    phoneInput.addEventListener('focus', function (e) {
      if (e.target.value === '+998 ' || e.target.value === '' || e.target.value === '+998') {
        e.target.value = '+998 ';
        setTimeout(() => e.target.setSelectionRange(5, 5), 0);
      }
    });

    phoneInput.addEventListener('click', function (e) {
      if (e.target.selectionStart < 5) {
        e.target.setSelectionRange(5, 5);
      }
    });

    phoneInput.addEventListener('keydown', function (e) {
      const cursorPos = e.target.selectionStart;

      if ((e.key === 'Backspace' || e.key === 'Delete') && cursorPos <= 5) {
        e.preventDefault();
        return false;
      }

      if (e.key === 'ArrowLeft' && cursorPos <= 5) {
        e.preventDefault();
        return false;
      }

      if (e.key === 'Home') {
        e.preventDefault();
        e.target.setSelectionRange(5, 5);
        return false;
      }
    });

    phoneInput.addEventListener('paste', function (e) {
      e.preventDefault();
      const pastedText = (e.clipboardData || window.clipboardData).getData('text');
      const numbers = pastedText.replace(/\D/g, '');

      let userNumbers = numbers;
      if (numbers.startsWith('998')) {
        userNumbers = numbers.substring(3);
      }

      userNumbers = userNumbers.substring(0, 9);
      this.value = formatPhone('998' + userNumbers);
    });
  }

  function initUniversalPhoneMask() {
    const phoneInputs = document.querySelectorAll('input[type="tel"], input[name="Phone"], input[id*="phone"]');

    if (phoneInputs.length === 0) return;


    phoneInputs.forEach((phoneInput, index) => {
      if (phoneInput.dataset.phoneMaskInitialized) return;
      initPhoneMask(phoneInput);
    });

  }

  // Инициализация только один раз при загрузке
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUniversalPhoneMask);
  } else {
    initUniversalPhoneMask();
  }
})();

// --------------------------------------------- //
// FAW Become a Dealer Form Handler
// --------------------------------------------- //

(function () {
  'use strict';

  function initDealerForm() {
    const dealerForm = document.getElementById('becomeADealerForm');

    if (!dealerForm) {
      return;
    }


    dealerForm.addEventListener('submit', async function (e) {
      e.preventDefault();

      const phoneInput = document.getElementById('dealer_phone');
      const phoneValue = phoneInput ? phoneInput.value.replace(/\D/g, '') : '';

      if (phoneValue.length !== 12 || !phoneValue.startsWith('998')) {
        alert('Iltimos, to\'g\'ri telefon raqam kiriting');
        phoneInput?.focus();
        return;
      }

      // Проверка сообщения
      const messageInput = document.getElementById('dealer_message');
      const messageValue = messageInput ? messageInput.value.trim() : '';
      if (!messageValue) {
        alert('Iltimos, xabar yozing');
        messageInput?.focus();
        return;
      }

      const btn = this.querySelector('button[type="submit"]');
      if (!btn) return;

      const originalHTML = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="btn-caption">Yuborilmoqda...</span>';

      try {
        let recaptchaToken;
        await grecaptcha.ready(() => {
          return grecaptcha.execute('6LecXTAsAAAAAN5LP2bcc7RHYV-0clG7B9p7KZow', { action: 'become_dealer' })
            .then(token => { recaptchaToken = token; });
        });

        const formData = {
          name: document.getElementById('dealer_name')?.value || '',
          company_name: document.getElementById('dealer_company')?.value || '',
          experience_years: parseInt(document.getElementById('dealer_experience')?.value) || null,
          region: document.getElementById('dealer_region')?.value || '',
          phone: '+' + phoneValue,
          message: messageValue,
          recaptcha_token: recaptchaToken  // ← ТОКЕН КАПЧИ
        };

        console.log('📤 Отправляем данные:', formData);

        const response = await fetch('/api/uz/dealer-applications/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
          },
          body: JSON.stringify(formData)
        });

        const data = await response.json();
        console.log('📨 Ответ сервера:', data);

        if (response.ok) {
          const replyDiv = document.querySelector('.form__reply');
          if (replyDiv) {
            replyDiv.style.display = 'block';
            setTimeout(() => replyDiv.style.display = 'none', 5000);
          }

          this.reset();
          if (phoneInput) phoneInput.value = '+998 ';
          alert('Arizangiz qabul qilindi!');

        } else {
          throw new Error(data.message || 'Xatolik yuz berdi');
        }
      } catch (error) {
        console.error('❌ Form error:', error);
        window.logJSError('Dealer form submission error: ' + error.message, {
          file: 'faw-scripts.js',
          formData: {
            name: document.getElementById('dealer_name')?.value,
            phone: '+' + phoneValue,
            region: document.getElementById('dealer_region')?.value
          }
        });
        alert('Xatolik yuz berdi. Iltimos qaytadan urinib ko\'ring.');
      }
      finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDealerForm);
  } else {
    initDealerForm();
  }
})();