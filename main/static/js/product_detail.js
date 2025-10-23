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
        if (!specsContainer) return;

        // Очищаем контейнер
        specsContainer.innerHTML = '';

        // Проверяем, есть ли параметры
        if (!this.product.spec_groups || this.product.spec_groups.length === 0) {
            specsContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: #888;">Parametrlar hali qo\'shilmagan</p>';
            return;
        }

        // Отображаем группы параметров (БЕЗ сортировки, порядок уже правильный из API)
        this.product.spec_groups.forEach((group, index) => {
            // Пропускаем пустые группы
            if (!group.parameters || group.parameters.length === 0) {
                return;
            }

            const isOpen = index === 0; // Первая группа открыта
            const groupHTML = this.createAccordionCard(group, index, isOpen);
            specsContainer.insertAdjacentHTML('beforeend', groupHTML);
        });

        // Если после фильтрации нет групп
        if (specsContainer.innerHTML === '') {
            specsContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: #888;">Parametrlar hali qo\'shilmagan</p>';
        }
    }

    createAccordionCard(group, index, isOpen) {
        // Дополнительная проверка на всякий случай
        if (!group.parameters || group.parameters.length === 0) {
            return '';
        }

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
            this.addGallerySlide(galleryContainer, this.product.main_image_url, this.product.title);
        } else {
            images.forEach(img => {
                this.addGallerySlide(galleryContainer, img.image_url, this.product.title);
            });
        }

        // ✅ ИСПОЛЬЗУЕМ imagesLoaded (уже есть в libs.min.js)
        const swiperContainer = document.querySelector('.mxd-demo-swiper');

        if (typeof imagesLoaded !== 'undefined') {
            imagesLoaded(galleryContainer, { background: true }, () => {
                console.log('Все изображения галереи загружены');
                this.initSwiper();
            });
        } else {
            // Фоллбэк если imagesLoaded недоступен
            this.waitForImages(galleryContainer).then(() => {
                this.initSwiper();
            });
        }
    }

    // Фоллбэк метод ожидания загрузки изображений
    waitForImages(container) {
        return new Promise((resolve) => {
            const images = container.querySelectorAll('img');
            if (images.length === 0) {
                resolve();
                return;
            }

            let loadedCount = 0;
            const totalImages = images.length;

            const checkComplete = () => {
                loadedCount++;
                if (loadedCount === totalImages) {
                    // Дополнительная задержка для стабильности
                    setTimeout(resolve, 100);
                }
            };

            images.forEach(img => {
                if (img.complete && img.naturalHeight !== 0) {
                    checkComplete();
                } else {
                    img.addEventListener('load', checkComplete);
                    img.addEventListener('error', checkComplete);
                }
            });
        });
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
        if (typeof Swiper === 'undefined') {
            console.error('Swiper не загружен');
            return;
        }

        // ✅ Уничтожаем предыдущий инстанс если есть
        const existingSwiper = document.querySelector('.mxd-demo-swiper')?.swiper;
        if (existingSwiper) {
            existingSwiper.destroy(true, true);
        }

        setTimeout(() => {
            const swiper = new Swiper('.mxd-demo-swiper', {
                // Breakpoints
                breakpoints: {
                    320: {
                        slidesPerView: 1,
                        spaceBetween: 20,
                    },
                    768: {
                        slidesPerView: 2,
                        spaceBetween: 30,
                    },
                    1024: {
                        slidesPerView: 3,
                        spaceBetween: 30,
                    },
                },

                // Loop settings
                loop: true,
                loopAdditionalSlides: 2, // Увеличили до 2
                loopedSlides: null, // Auto-calculate

                // Core
                centeredSlides: true,
                initialSlide: 0,
                speed: 600,
                grabCursor: true,

                // Autoplay - ОТКЛЮЧАЕМ при старте
                autoplay: false, // ⚠️ Включим после init

                // Features
                parallax: true,
                keyboard: { enabled: true },

                // Navigation
                navigation: {
                    nextEl: '.swiper-button-next',
                    prevEl: '.swiper-button-prev',
                },

                // Observers
                observer: true,
                observeParents: true,
                observeSlideChildren: true,

                // Sizing
                watchOverflow: true,
                watchSlidesProgress: true,
                watchSlidesVisibility: true,

                // Prevent issues
                preventInteractionOnTransition: true,
                touchRatio: 1,
                touchAngle: 45,

                // Callbacks
                on: {
                    init: function () {
                        console.log('Swiper инициализирован');

                        // ✅ Принудительное обновление после init
                        setTimeout(() => {
                            this.update();
                            this.slideToLoop(0, 0); // Перейти на первый слайд без анимации

                            // ✅ ВКЛЮЧАЕМ autoplay ПОСЛЕ полной инициализации
                            if (this.params.autoplay !== false) {
                                this.params.autoplay = {
                                    delay: 3000,
                                    disableOnInteraction: false,
                                };
                                this.autoplay.start();
                            }
                        }, 200);
                    },

                    slideChangeTransitionStart: function () {
                        // Останавливаем parallax во время transition для стабильности
                        this.params.parallax = false;
                    },

                    slideChangeTransitionEnd: function () {
                        // Включаем parallax обратно
                        this.params.parallax = true;
                        this.update();
                    },
                }
            });

            // Сохраняем ссылку на swiper
            window.gallerySwiper = swiper;

            console.log('Swiper создан, количество слайдов:', swiper.slides.length);
        }, 200); // Увеличили задержку до 200ms
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