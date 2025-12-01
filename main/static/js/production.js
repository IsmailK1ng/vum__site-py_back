/**
 * FAW Products - Динамическая загрузка карточек с поддержкой переводов
 * Обновлено: поддержка множественных категорий
 */

class ProductsManager {
  constructor() {
    // Определяем текущий язык
    this.currentLanguage = document.documentElement.lang ||
      window.LANGUAGE_CODE ||
      this.getCookie('django_language') ||
      'uz';

    // Определяем API URL в зависимости от языка
    this.apiUrl = `/api/${this.currentLanguage}/products/`;
    this.currentCategory = null;
    this.currentPage = 1;
    this.cardsPerPage = 8;
    this.allProducts = [];
    this.filteredProducts = [];

    // Полная информация о категориях с переводами
    this.categoryTranslations = {
      'tiger_vh': {
        uz: {
          title: 'Tiger VH',
          breadcrumb: 'Tiger VH',
          slogan: 'Ikki yoqilg\'ida harakatlanuvchi texnika',
          buttonText: 'Batafsil o\'qish'
        },
        ru: {
          title: 'Tiger VH',
          breadcrumb: 'Tiger VH',
          slogan: 'Техника на двух видах топлива',
          buttonText: 'Подробнее'
        },
        en: {
          title: 'Tiger VH',
          breadcrumb: 'Tiger VH',
          slogan: 'Dual-fuel technology',
          buttonText: 'Read more'
        },
        hero_image: 'images/categories/vh_models.png'
      },
      'samosval': {
        uz: {
          title: 'Samosvallar',
          breadcrumb: 'Samosvallar',
          slogan: 'Qurilish uchun eng yaxshi yechim',
          buttonText: 'Batafsil o\'qish'
        },
        ru: {
          title: 'Самосвалы',
          breadcrumb: 'Самосвалы',
          slogan: 'Лучшее решение для строительства',
          buttonText: 'Подробнее'
        },
        en: {
          title: 'Dump Trucks',
          breadcrumb: 'Dump Trucks',
          slogan: 'Best solution for construction',
          buttonText: 'Read more'
        },
        hero_image: 'images/categories/dump-truck-hero.png'
      },
      'maxsus': {
        uz: {
          title: 'Maxsus texnika',
          breadcrumb: 'Maxsus texnika',
          slogan: 'Har qanday vazifa uchun',
          buttonText: 'Batafsil o\'qish'
        },
        ru: {
          title: 'Спецтехника',
          breadcrumb: 'Спецтехника',
          slogan: 'Для любых задач',
          buttonText: 'Подробнее'
        },
        en: {
          title: 'Special Equipment',
          breadcrumb: 'Special Equipment',
          slogan: 'For any task',
          buttonText: 'Read more'
        },
        hero_image: 'images/categories/special-hero.png'
      },
      'furgon': {
        uz: {
          title: 'Avtofurgonlar',
          breadcrumb: 'Avtofurgonlar',
          slogan: 'Yuk tashish uchun ideal',
          buttonText: 'Batafsil o\'qish'
        },
        ru: {
          title: 'Фургоны',
          breadcrumb: 'Фургоны',
          slogan: 'Идеально для перевозки грузов',
          buttonText: 'Подробнее'
        },
        en: {
          title: 'Vans',
          breadcrumb: 'Vans',
          slogan: 'Perfect for cargo transportation',
          buttonText: 'Read more'
        },
        hero_image: 'images/categories/avtofurgon-hero.png'
      },
      'shassi': {
        uz: {
          title: 'Shassilar',
          breadcrumb: 'Shassilar',
          slogan: 'Ishonchli asos',
          buttonText: 'Batafsil o\'qish'
        },
        ru: {
          title: 'Шасси',
          breadcrumb: 'Шасси',
          slogan: 'Надежная основа',
          buttonText: 'Подробнее'
        },
        en: {
          title: 'Chassis',
          breadcrumb: 'Chassis',
          slogan: 'Reliable foundation',
          buttonText: 'Read more'
        },
        hero_image: 'images/categories/chassis-hero.png'
      },
      'tiger_v': {
        uz: {
          title: 'Tiger V',
          breadcrumb: 'Tiger V',
          slogan: 'Kuchli va zamonaviy pikap',
          buttonText: 'Batafsil o\'qish'
        },
        ru: {
          title: 'Tiger V',
          breadcrumb: 'Tiger V',
          slogan: 'Мощный и современный пикап',
          buttonText: 'Подробнее'
        },
        en: {
          title: 'Tiger V',
          breadcrumb: 'Tiger V',
          slogan: 'Powerful and modern pickup',
          buttonText: 'Read more'
        },
        hero_image: 'images/categories/tiger-v-hero.png'
      },
      'tiger_vr': {
        uz: {
          title: 'Tiger VR',
          breadcrumb: 'Tiger VR',
          slogan: 'Shahar ichida ishlash uchun ideal texnika',
          buttonText: 'Batafsil o\'qish'
        },
        ru: {
          title: 'Tiger VR',
          breadcrumb: 'Tiger VR',
          slogan: 'Идеальная техника для работы внутри города',
          buttonText: 'Подробнее'
        },
        en: {
          title: 'Tiger VR',
          breadcrumb: 'Tiger VR',
          slogan: 'Ideal equipment for working within the city',
          buttonText: 'Read more'
        },
        hero_image: 'images/categories/tiger-vr-hero.png'
      }
    };

    this.init();
  }

  // Определяем API URL в зависимости от текущего языка
  getApiUrl() {
    return `/api/${this.currentLanguage}/products/`;
  }

  // Получаем данные категории на текущем языке
  getCategoryData(categoryKey) {
    const category = this.categoryTranslations[categoryKey];
    if (!category) return null;

    const langData = category[this.currentLanguage] || category['uz'];
    return {
      ...langData,
      hero_image: category.hero_image
    };
  }

  // Получаем cookie
  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  async init() {
    // Получаем категорию из URL
    const urlParams = new URLSearchParams(window.location.search);
    this.currentCategory = urlParams.get('category');

    // Обновляем все элементы страницы
    this.updatePageContent();

    // Загружаем продукты
    await this.loadProducts();

    // Инициализируем поиск
    this.initSearch();
  }

  updatePageContent() {
    if (!this.currentCategory) {
      console.log('No category specified');
      return;
    }

    const categoryInfo = this.getCategoryData(this.currentCategory);
    if (!categoryInfo) {
      console.error('Unknown category:', this.currentCategory);
      return;
    }

    // 1. Обновляем главный заголовок
    const titleElement = document.querySelector('.models_title');
    if (titleElement) {
      titleElement.textContent = categoryInfo.title;
    }

    // 2. Обновляем слоган
    const sloganElement = document.querySelector('.hero-05-title__item:not(.title-item-image)');
    if (sloganElement) {
      sloganElement.textContent = categoryInfo.slogan;
    }

    // 3. Обновляем hero изображение
    const heroImage = document.querySelector('.mxd-hero-06__img img');
    if (heroImage && categoryInfo.hero_image) {
      const staticPath = `/static/${categoryInfo.hero_image}`;

      // Проверяем существование изображения
      const testImg = new Image();
      testImg.onload = () => {
        heroImage.src = staticPath;
        heroImage.alt = categoryInfo.title;
      };
      testImg.onerror = () => {
        // Если нет - оставляем текущее или ставим заглушку
        console.warn(`Hero image not found: ${staticPath}`);
      };
      testImg.src = staticPath;
    }

    // 4. Обновляем хлебные крошки
    const breadcrumbActive = document.querySelector('.breadcrumb-ol .active a');
    if (breadcrumbActive) {
      breadcrumbActive.textContent = categoryInfo.breadcrumb;
    }

    // 5. Обновляем title страницы
    document.title = `${categoryInfo.title} - FAW Trucks`;

    // Сохраняем текст кнопки для использования в карточках
    this.buttonText = categoryInfo.buttonText;
  }

  async loadProducts() {
    try {
      this.showLoader();

      // ✅ Загружаем ВСЕ страницы
      let allProducts = [];
      let nextUrl = this.apiUrl;

      while (nextUrl) {
        const response = await fetch(nextUrl);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Добавляем продукты из текущей страницы
        const products = data.results || data.products || data || [];
        allProducts = allProducts.concat(products);

        // ✅ ИСПРАВЛЕНИЕ: Приводим URL к HTTPS
           // Приводим URL к текущему протоколу (http/https)
        if (data.next) {
          // Используем относительный URL вместо абсолютного
          try {
            const url = new URL(data.next);
            nextUrl = url.pathname + url.search;
          } catch (e) {
            nextUrl = data.next;
          }
        } else {
          nextUrl = null;
        }
      }

      this.allProducts = allProducts;

      console.log(`✅ Загружено ${this.allProducts.length} продуктов`);

      // ФИЛЬТРУЕМ продукты по категории на фронтенде
      if (this.currentCategory) {
        this.filteredProducts = this.allProducts.filter(product => {
          if (product.category === this.currentCategory) {
            return true;
          }
          if (product.all_categories && Array.isArray(product.all_categories)) {
            return product.all_categories.some(cat => cat.slug === this.currentCategory);
          }
          return false;
        });

        console.log(`✅ Найдено ${this.filteredProducts.length} продуктов в категории "${this.currentCategory}"`);
      } else {
        this.filteredProducts = [...this.allProducts];
      }

      if (this.filteredProducts.length === 0) {
        this.showNoResults();
        return;
      }

      this.renderCards();
      this.createPagination();
      this.hideLoader();

    } catch (error) {
      console.error('Products loading error:', error);
      if (window.logJSError) {
        window.logJSError('Products loading error: ' + error.message, {
          file: 'products.js',
          category: this.currentCategory,
          url: this.apiUrl
        });
      }
      this.showError(error.message);
    }
  }

  renderCards() {
    const container = document.querySelector('.faw-truck-card-container');
    if (!container) {
      window.logJSError('Container .faw-truck-card-container not found', { file: 'products.js' });
      return;
    }

    container.innerHTML = '';

    const start = (this.currentPage - 1) * this.cardsPerPage;
    const end = start + this.cardsPerPage;
    const cardsToShow = this.filteredProducts.slice(start, end);

    if (cardsToShow.length === 0) {
      this.showNoResults();
      return;
    }

    cardsToShow.forEach(product => {
      const cardHTML = this.createCardHTML(product);
      const wrapper = document.createElement('div');
      wrapper.className = 'product-card-wrapper';
      wrapper.innerHTML = cardHTML;
      container.appendChild(wrapper);
    });
  }

  createCardHTML(product) {
    // Проверяем наличие спецификаций
    let specsHTML = '';
    if (product.card_specs && Array.isArray(product.card_specs)) {
      specsHTML = product.card_specs
        .sort((a, b) => (a.order || 0) - (b.order || 0))
        .map(spec => {
          const iconUrl = spec.icon?.icon_url || spec.icon_url || '';
          const iconName = spec.icon?.name || spec.name || '';
          const specValue = spec.value || '';
          return `
            <div class="spec-item">
              ${iconUrl ? `<img class="spec-icon" src="${iconUrl}" alt="${iconName}">` : ''}
              <span class="spec-value">${specValue}</span>
            </div>
          `;
        }).join('');
    }

    // Формируем URL изображения
    const imageUrl = product.image_url || product.image || product.main_image || '';
    const productSlug = product.slug || '';
    const productTitle = product.title || product.name || 'Продукт';
    const buttonText = this.buttonText || 'Подробнее';

    return `
      <div class="faw-truck-card">
        <div class="truck-image-container">
          ${imageUrl ? `<img src="${imageUrl}" alt="${productTitle}" class="truck-image">` : ''}
        </div>
        <div class="truck-info">
          <h3 class="truck-title">${productTitle}</h3>
          ${specsHTML ? `<div class="truck-specs">${specsHTML}</div>` : ''}
          <div class="truck-cta">
            <a href="/products/${productSlug}/" class="btn-details">${buttonText}</a>
          </div>
        </div>
      </div>
    `;
  }

  createPagination() {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;

    const totalPages = Math.ceil(this.filteredProducts.length / this.cardsPerPage);

    if (totalPages <= 1) {
      pagination.innerHTML = '';
      return;
    }

    pagination.innerHTML = '';

    // Кнопка "Назад"
    const prevButton = this.createButton('prev', 'Ortga', this.currentPage > 1);
    prevButton.addEventListener('click', (e) => {
      e.preventDefault();
      if (this.currentPage > 1) {
        this.currentPage--;
        this.renderCards();
        this.updatePagination();
        this.scrollToTop();
      }
    });
    pagination.appendChild(prevButton);

    // Номера страниц
    for (let i = 1; i <= totalPages; i++) {
      const pageButton = document.createElement('a');
      pageButton.href = 'javascript:void(0);';
      pageButton.className = `mxd-blog-pagination__item blog-pagination-number btn btn-anim ${i === this.currentPage ? 'active' : ''}`;
      pageButton.innerHTML = `<span class="btn-caption">${i}</span>`;
      pageButton.addEventListener('click', (e) => {
        e.preventDefault();
        this.currentPage = i;
        this.renderCards();
        this.updatePagination();
        this.scrollToTop();
      });
      pagination.appendChild(pageButton);
    }

    // Кнопка "Вперед"
    const nextButton = this.createButton('next', 'Oldinga', this.currentPage < totalPages);
    nextButton.addEventListener('click', (e) => {
      e.preventDefault();
      if (this.currentPage < totalPages) {
        this.currentPage++;
        this.renderCards();
        this.updatePagination();
        this.scrollToTop();
      }
    });
    pagination.appendChild(nextButton);
  }

  createButton(type, text, enabled) {
    const button = document.createElement('a');
    button.href = 'javascript:void(0);';
    button.className = `mxd-blog-pagination__item blog-pagination-control ${type} btn btn-anim btn-line-small btn-bright anim-no-delay slide-${type === 'prev' ? 'left' : 'right'}`;

    if (!enabled) button.classList.add('disabled');

    if (type === 'prev') {
      button.innerHTML = `<i class="ph ph-arrow-left"></i><span class="btn-caption">${text}</span>`;
    } else {
      button.innerHTML = `<span class="btn-caption">${text}</span><i class="ph ph-arrow-right"></i>`;
    }

    return button;
  }

  updatePagination() {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;

    const pageButtons = pagination.querySelectorAll('.blog-pagination-number');
    pageButtons.forEach(btn => {
      const pageNum = parseInt(btn.querySelector('.btn-caption').textContent);
      btn.classList.toggle('active', pageNum === this.currentPage);
    });

    const prevButton = pagination.querySelector('.prev');
    const nextButton = pagination.querySelector('.next');
    const totalPages = Math.ceil(this.filteredProducts.length / this.cardsPerPage);

    if (prevButton) prevButton.classList.toggle('disabled', this.currentPage === 1);
    if (nextButton) nextButton.classList.toggle('disabled', this.currentPage === totalPages);
  }

  initSearch() {
    const searchInput = document.querySelector('.filter-search__input');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();

      if (query === '') {
        // ✅ Сбрасываем на отфильтрованные по категории продукты
        if (this.currentCategory) {
          this.filteredProducts = this.allProducts.filter(product => {
            if (product.category === this.currentCategory) {
              return true;
            }
            if (product.all_categories && Array.isArray(product.all_categories)) {
              return product.all_categories.some(cat => cat.slug === this.currentCategory);
            }
            return false;
          });
        } else {
          this.filteredProducts = [...this.allProducts];
        }
      } else {
        // ✅ Ищем среди уже отфильтрованных по категории продуктов
        const categoryFiltered = this.currentCategory
          ? this.allProducts.filter(product => {
            if (product.category === this.currentCategory) {
              return true;
            }
            if (product.all_categories && Array.isArray(product.all_categories)) {
              return product.all_categories.some(cat => cat.slug === this.currentCategory);
            }
            return false;
          })
          : this.allProducts;

        this.filteredProducts = categoryFiltered.filter(product => {
          const title = (product.title || product.name || '').toLowerCase();
          return title.includes(query);
        });
      }

      this.currentPage = 1;
      this.renderCards();
      this.createPagination();
    });
  }

  scrollToTop() {
    const header = document.getElementById('header');
    const headerHeight = header ? header.offsetHeight : 0;
    const offset = 25;

    window.scrollTo({
      top: Math.max(0, headerHeight + offset),
      behavior: 'smooth'
    });
  }

  showLoader() {
    const container = document.querySelector('.faw-truck-card-container');
    if (container) {
      container.innerHTML = '<div class="loader-container"><div class="loader">Yuklanmoqda...</div></div>';
    }
  }

  hideLoader() {
    const loader = document.querySelector('.loader-container');
    if (loader) loader.remove();
  }

  showNoResults() {
    const container = document.querySelector('.faw-truck-card-container');
    if (container) {
      container.innerHTML = '<div class="no-results"><p>Mahsulotlar topilmadi</p></div>';
    }
    const pagination = document.getElementById('pagination');
    if (pagination) pagination.innerHTML = '';
  }

  showError(message) {
    const container = document.querySelector('.faw-truck-card-container');
    if (container) {
      container.innerHTML = `
        <div class="error-message">
          <p>Xatolik yuz berdi: ${message}</p>
          <p>Keyinroq urinib ko'ring yoki sahifani yangilang.</p>
        </div>
      `;
    }
  }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
  new ProductsManager();
});