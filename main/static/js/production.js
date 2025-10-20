/**
 * FAW Products - Динамическая загрузка карточек
 */

class ProductsManager {
  constructor() {
    this.apiUrl = '/api/uz/products/';
    this.currentCategory = null;
    this.currentPage = 1;
    this.cardsPerPage = 6;
    this.allProducts = [];
    this.filteredProducts = [];
    
    this.init();
  }

  async init() {
    // Получаем категорию из URL
    const urlParams = new URLSearchParams(window.location.search);
    this.currentCategory = urlParams.get('category');
    
    // Загружаем продукты
    await this.loadProducts();
    
    // Инициализируем поиск
    this.initSearch();
  }

  async loadProducts() {
    try {
      this.showLoader();
      
      // Формируем URL с категорией
      let url = this.apiUrl;
      if (this.currentCategory) {
        url += `?category=${this.currentCategory}`;
      }
      
      const response = await fetch(url);
      const data = await response.json();
      
      this.allProducts = data.results || [];
      this.filteredProducts = [...this.allProducts];
      
      this.renderCards();
      this.createPagination();
      this.hideLoader();
      
    } catch (error) {
      console.error('Ошибка загрузки:', error);
      this.showError();
    }
  }

  renderCards() {
    const container = document.querySelector('.faw-truck-card-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    const start = (this.currentPage - 1) * this.cardsPerPage;
    const end = start + this.cardsPerPage;
    const cardsToShow = this.filteredProducts.slice(start, end);
    
    if (cardsToShow.length === 0) {
      container.innerHTML = '<div class="no-results"><p>Mahsulotlar topilmadi</p></div>';
      return;
    }
    
    cardsToShow.forEach(product => {
      const cardHTML = this.createCardHTML(product);
      container.insertAdjacentHTML('beforeend', cardHTML);
    });
  }

  createCardHTML(product) {
    const specsHTML = product.card_specs
      .sort((a, b) => a.order - b.order)
      .map(spec => `
        <div class="spec-item">
          <img class="spec-icon" src="${spec.icon.icon_url}" alt="${spec.icon.name}">
          <span class="spec-value">${spec.value}</span>
        </div>
      `).join('');

    return `
      <div class="faw-truck-card">
        <div class="truck-image-container">
          <img src="${product.image_url}" alt="${product.title}" class="truck-image">
        </div>
        <div class="truck-info">
          <h3 class="truck-title">${product.title}</h3>
          <div class="truck-specs">
            ${specsHTML}
          </div>
          <div class="truck-cta">
            <a href="/products/${product.slug}/" class="btn-details">Batafsil o'qish</a>
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
        this.filteredProducts = this.allProducts.filter(product => 
          product.title.toLowerCase().includes(query)
        );
      }
      
      this.currentPage = 1;
      this.renderCards();
      this.createPagination();
    });
  }

  scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
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

  showError() {
    const container = document.querySelector('.faw-truck-card-container');
    if (container) {
      container.innerHTML = '<div class="error-message"><p>Xatolik yuz berdi. Keyinroq urinib ko\'ring.</p></div>';
    }
  }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
  new ProductsManager();
});