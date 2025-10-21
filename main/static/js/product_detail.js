/**
 * FAW Product Detail - Загрузка детальной информации о продукте
 */

class ProductDetail {
    constructor() {
        this.productId = null;
        this.apiUrl = '/api/uz/products/';
        this.product = null;

        this.init();
    }

    async init() {
        // Получаем slug из URL
        const pathParts = window.location.pathname.split('/').filter(p => p);
        const slug = pathParts[pathParts.length - 1];

        if (!slug) {
            this.showError('Mahsulot topilmadi');
            return;
        }

        await this.loadProduct(slug);
    }

    async loadProduct(slug) {
        try {
            this.showLoader();

            const response = await fetch(`${this.apiUrl}${slug}/`);

            if (!response.ok) {
                throw new Error('Mahsulot topilmadi');
            }

            const data = await response.json();
            this.product = data;

            this.renderProduct();
            this.hideLoader();

        } catch (error) {
            console.error('Ошибка загрузки:', error);
            this.showError('Mahsulot yuklanmadi. Qayta urinib ko\'ring.');
        }
    }

    renderProduct() {
        // 1. Заголовок и категория
        document.querySelector('.models_title').textContent = this.product.title;

        // ✅ СОХРАНЯЕМ НАЗВАНИЕ ПРОДУКТА В ГЛОБАЛЬНУЮ ПЕРЕМЕННУЮ
        window.currentProductTitle = this.product.title;

        // 2. Главное изображение
        const heroImg = document.querySelector('.mxd-hero-06__car-image');
        if (heroImg && this.product.main_image_url) {
            heroImg.src = this.product.main_image_url;
            heroImg.alt = this.product.title;
        }

        // 3. 8 характеристик с иконками
        this.renderFeatures();

        // 4. Параметры (accordion)
        this.renderSpecifications();

        // 5. Галерея
        this.renderGallery();

        // 6. Обновляем хлебные крошки
        this.updateBreadcrumbs();
    }

    renderFeatures() {
        const featuresContainer = document.querySelector('.car-specs-grid');
        if (!featuresContainer || !this.product.features) return;

        // Очищаем контейнер
        featuresContainer.innerHTML = '';

        // Сортируем по order и берем первые 8
        const features = this.product.features
            .sort((a, b) => a.order - b.order)
            .slice(0, 8);

        features.forEach(feature => {
            const featureHTML = `
                <div class="car-spec-item">
                    <img src="${feature.icon.icon_url}" class="car-spec-icon" alt="${feature.icon.name}">
                    <div class="car-spec-content">
                        <div class="car-spec-label">${feature.name}</div>
                        <div class="car-spec-value">Mavjud</div>
                    </div>
                </div>
            `;
            featuresContainer.insertAdjacentHTML('beforeend', featureHTML);
        });
    }

    renderSpecifications() {
        const specsContainer = document.querySelector('.acardeon-cards_block');
        if (!specsContainer || !this.product.spec_groups) return;

        // Очищаем контейнер
        specsContainer.innerHTML = '';

        // Сортируем группы по order
        const groups = this.product.spec_groups.sort((a, b) => a.order - b.order);

        groups.forEach((group, index) => {
            const isOpen = index === 0; // Первая группа открыта
            const groupHTML = this.createAccordionCard(group, index, isOpen);
            specsContainer.insertAdjacentHTML('beforeend', groupHTML);
        });
    }

    createAccordionCard(group, index, isOpen) {
        const parameters = group.parameters
            .sort((a, b) => a.order - b.order)
            .map(param => `<li class="specs-list__item">${param.text}</li>`)
            .join('');

        return `
            <div class="acardeon-card">
                <input type="checkbox" id="accordion-${index}" class="accordion-checkbox" ${isOpen ? 'checked' : ''}>
                <label for="accordion-${index}" class="acardeon-card__header">
                    <h3 class="acardeon-card__title">${group.category_name}</h3>
                    <span class="acardeon-card__icon"></span>
                </label>
                <div class="acardeon-card__content">
                    <ul class="specs-list custom-marker">
                        ${parameters}
                    </ul>
                </div>
            </div>
        `;
    }

    renderGallery() {
        const galleryContainer = document.querySelector('.swiper-wrapper');
        if (!galleryContainer || !this.product.gallery) return;

        // Очищаем контейнер
        galleryContainer.innerHTML = '';

        // Сортируем по order
        const images = this.product.gallery.sort((a, b) => a.order - b.order);

        if (images.length === 0) {
            // Если нет изображений, показываем главное
            this.addGallerySlide(galleryContainer, this.product.main_image_url, this.product.title);
            return;
        }

        images.forEach(img => {
            this.addGallerySlide(galleryContainer, img.image_url, this.product.title);
        });

        // Переинициализируем Swiper
        this.initSwiper();
    }

    addGallerySlide(container, imageUrl, alt) {
        const slideHTML = `
            <div class="swiper-slide mxd-demo-swiper__slide">
                <div class="slide-content">
                    <div class="slide-image">
                        <img src="${imageUrl}" alt="${alt}">
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', slideHTML);
    }

    initSwiper() {
        // Проверяем, есть ли Swiper в libs
        if (typeof Swiper !== 'undefined') {
            setTimeout(() => {
                new Swiper('.mxd-demo-swiper', {
                    slidesPerView: 1,
                    spaceBetween: 30,
                    loop: true,
                    navigation: {
                        nextEl: '.swiper-button-next',
                        prevEl: '.swiper-button-prev',
                    },
                });
            }, 100);
        }
    }

    updateBreadcrumbs() {
        const breadcrumbLinks = document.querySelectorAll('.breadcrumb-ol li a');
        if (breadcrumbLinks.length >= 3) {
            // Обновляем последнюю крошку с названием продукта
            breadcrumbLinks[2].textContent = this.product.title;
            breadcrumbLinks[2].href = 'javascript:void(0)';

            // Обновляем ссылку на категорию
            if (this.product.category) {
                breadcrumbLinks[1].href = `/products/?category=${this.product.category}`;
                breadcrumbLinks[1].textContent = this.product.category_display;
            }
        }
    }

    showLoader() {
        const loader = document.createElement('div');
        loader.id = 'product-loader';
        loader.className = 'page-loader';
        loader.innerHTML = '<div class="loader">Yuklanmoqda...</div>';
        document.body.appendChild(loader);
    }

    hideLoader() {
        const loader = document.getElementById('product-loader');
        if (loader) {
            loader.remove();
        }
    }

    showError(message) {
        this.hideLoader();
        const content = document.querySelector('.mxd-page-content');
        if (content) {
            content.innerHTML = `
                <div class="error-page">
                    <div class="grid-container">
                        <div class="error-content">
                            <h1>❌ Xatolik</h1>
                            <p>${message}</p>
                            <a href="/products/?category=tractor" class="btn btn-primary">
                                <span>Bosh sahifaga qaytish</span>
                            </a>
                        </div>
                    </div>
                </div>
            `;
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new ProductDetail();
});