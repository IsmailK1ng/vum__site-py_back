/**
 * FAW Products - Динамическая загрузка карточек
 */

class ProductsManager {
  constructor() {
    // API endpoint - проверьте правильный путь
    this.apiUrl = '/api/uz/products/'; 
    this.currentCategory = null;
    this.currentPage = 1;
    this.cardsPerPage = 6;
    this.allProducts = [];
    this.filteredProducts = [];
    
    // Полная информация о категориях с картинками и слоганами
    this.categoryData = {
      'shatakchi': {
        title: 'Shatakchi mashinalar',
        breadcrumb: 'Shatakchi mashinalar',
        slogan: 'Kuchli va ishonchli tortuvchilar',
        hero_image: 'images/categories/tractor-hero.png' // Укажите правильный путь
      },
      'samosval': {
        title: 'Samosvallar',
        breadcrumb: 'Samosvallar',
        slogan: 'Qurilish uchun eng yaxshi yechim',
        hero_image: 'images/categories/dump-truck-hero.png'
      },
      'maxsus': {
        title: 'Maxsus texnika',
        breadcrumb: 'Maxsus texnika',
        slogan: 'Har qanday vazifa uchun',
        hero_image: 'images/categories/special-hero.png'
      },
      'furgon': {
        title: 'Avtofurgonlar',
        breadcrumb: 'Avtofurgonlar',
        slogan: 'Yuk tashish uchun ideal',
        hero_image: 'images/categories/avtofurgon-hero.png'
      },
      'shassi': {
        title: 'Shassilar',
        breadcrumb: 'Shassilar',
        slogan: 'Ishonchli asos',
        hero_image: 'images/categories/chassis-hero.png'
      },
      'tiger_v': {
        title: 'Tiger V',
        breadcrumb: 'Tiger V',
        slogan: 'Kuchli va zamonaviy pikap',
        hero_image: 'images/categories/tiger-v-hero.png'
      },
      'tiger_vr': {
        title: 'Tiger VR',
        breadcrumb: 'Tiger VR',
        slogan: 'Premium sinf pikap',
        hero_image: 'images/categories/tiger-vr-hero.png'
      }
    };
    
    this.init();
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
    
    const categoryInfo = this.categoryData[this.currentCategory];
    if (!categoryInfo) {
      console.error('Unknown category:', this.currentCategory);
      return;
    }
    
    console.log('Updating page for category:', this.currentCategory, categoryInfo);
    
    // 1. Обновляем главный заголовок
    const titleElement = document.querySelector('.models_title');
    if (titleElement) {
      titleElement.textContent = categoryInfo.title;
      console.log('✓ Title updated');
    }
    
    // 2. Обновляем слоган
    const sloganElement = document.querySelector('.hero-05-title__item:not(.title-item-image)');
    if (sloganElement) {
      sloganElement.textContent = categoryInfo.slogan;
      console.log('✓ Slogan updated');
    }
    
    // 3. Обновляем hero изображение
    const heroImage = document.querySelector('.mxd-hero-06__img img');
    if (heroImage) {
      // Используем полный путь через static
      const staticPath = `/static/${categoryInfo.hero_image}`;
      heroImage.src = staticPath;
      heroImage.alt = categoryInfo.title;
      console.log('✓ Hero image updated:', staticPath);
    }
    
    // 4. Обновляем хлебные крошки
    const breadcrumbActive = document.querySelector('.breadcrumb-ol .active a');
    if (breadcrumbActive) {
      breadcrumbActive.textContent = categoryInfo.breadcrumb;
      console.log('✓ Breadcrumb updated');
    }
    
    // 5. Обновляем title страницы
    document.title = `${categoryInfo.title} - FAW Trucks`;
    console.log('✓ Page title updated');
  }

  async loadProducts() {
    try {
      this.showLoader();
      
      // Формируем URL с категорией
      let url = this.apiUrl;
      if (this.currentCategory) {
        url += `?category=${this.currentCategory}`;
      }
      
      console.log('Loading products from:', url);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Products loaded:', data);
      
      // Поддержка разных форматов ответа
      this.allProducts = data.results || data.products || data || [];
      this.filteredProducts = [...this.allProducts];
      
      if (this.allProducts.length === 0) {
        this.showNoResults();
        return;
      }
      
      this.renderCards();
      this.createPagination();
      this.hideLoader();
      
    } catch (error) {
      console.error('Ошибка загрузки:', error);
      this.showError(error.message);
    }
  }

  renderCards() {
    const container = document.querySelector('.faw-truck-card-container');
    if (!container) {
      console.error('Container .faw-truck-card-container not found');
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
      wrapper.className = 'col-12 col-xl-4 mxd-grid-item animate-card-3';
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
          return `
            <div class="spec-item">
              ${iconUrl ? `<img class="spec-icon" src="${iconUrl}" alt="${iconName}">` : ''}
              <span class="spec-value">${spec.value || ''}</span>
            </div>
          `;
        }).join('');
    }

    // Формируем URL изображения
    const imageUrl = product.image_url || product.image || product.main_image || '';
    const productSlug = product.slug || '';
    const productTitle = product.title || product.name || 'Продукт';

    return `
      <div class="faw-truck-card">
        <div class="truck-image-container">
          ${imageUrl ? `<img src="${imageUrl}" alt="${productTitle}" class="truck-image">` : ''}
        </div>
        <div class="truck-info">
          <h3 class="truck-title">${productTitle}</h3>
          ${specsHTML ? `<div class="truck-specs">${specsHTML}</div>` : ''}
          <div class="truck-cta">
            <a href="/products/${productSlug}/" class="btn-details">Batafsil o'qish</a>
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
        this.filteredProducts = [...this.allProducts];
      } else {
        this.filteredProducts = this.allProducts.filter(product => {
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