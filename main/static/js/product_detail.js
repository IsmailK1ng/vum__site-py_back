/**
 * FAW Product Detail - Production Version with Full Translation Support
 */

class ProductDetail {
    constructor() {
        this.productId = null;


    this.currentLanguage = (document.documentElement.lang ||
        window.LANGUAGE_CODE ||
        this.getCookie('django_language') ||
        'uz').split('-')[0];

        this.apiUrl = this.getApiUrl();
        this.product = null;

        // Переводы для категорий и текстов
        this.translations = {
            uz: {
                loading: 'Yuklanmoqda...',
                error: 'Xatolik',
                notFound: 'Mahsulot topilmadi',
                loadError: 'Mahsulot yuklanmadi. Qayta urinib ko\'ring.',
                backToHome: 'Bosh sahifaga qaytish',
                noParams: 'Parametrlar hali qo\'shilmagan',
                categories: {
                    'samosval': 'Samosvallar',
                    'maxsus': 'Maxsus texnika',
                    'furgon': 'Avtofurgonlar',
                    'shassi': 'Shassilar',
                    'tiger_v': 'Tiger V',
                    'tiger_vh': 'Tiger VH',
                    'tiger_vr': 'Tiger VR'
                }
            },
            ru: {
                loading: 'Загрузка...',
                error: 'Ошибка',
                notFound: 'Продукт не найден',
                loadError: 'Не удалось загрузить продукт. Попробуйте снова.',
                backToHome: 'Вернуться на главную',
                noParams: 'Параметры пока не добавлены',
                categories: {
                    'samosval': 'Самосвалы',
                    'maxsus': 'Спецтехника',
                    'furgon': 'Фургоны',
                    'shassi': 'Шасси',
                    'tiger_v': 'Tiger V',
                    'tiger_vh': 'Tiger VH',
                    'tiger_vr': 'Tiger VR'
                }
            },
            en: {
                loading: 'Loading...',
                error: 'Error',
                notFound: 'Product not found',
                loadError: 'Failed to load product. Please try again.',
                backToHome: 'Back to home',
                noParams: 'Parameters not yet added',
                categories: {
                    'samosval': 'Dump Trucks',
                    'maxsus': 'Special Equipment',
                    'furgon': 'Vans',
                    'shassi': 'Chassis',
                    'tiger_v': 'Tiger V',
                    'tiger_vh': 'Tiger VH',
                    'tiger_vr': 'Tiger VR'
                }
            }
        };

        this.init();
    }

    // Определяем API URL в зависимости от текущего языка
    getApiUrl() {
        return `/api/${this.currentLanguage}/products/`;
    }

    // Получаем перевод
    t(key) {
        const keys = key.split('.');
        let value = this.translations[this.currentLanguage];

        for (const k of keys) {
            value = value?.[k];
        }

        return value || key;
    }

    // Получаем cookie
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    async init() {
        // 🔍 DEBUG
        console.log('Full URL:', window.location.href);
        console.log('Pathname:', window.location.pathname);
        console.log('Search params:', window.location.search);
        
        const pathParts = window.location.pathname.split('/').filter(p => p);
        const slug = pathParts[pathParts.length - 1];
        
        console.log('Path parts:', pathParts);
        console.log('Extracted slug:', slug);

        
        if (!slug) {
            this.showError(this.t('notFound'));
            return;
        }

        await this.loadProduct(slug);
    }

    async loadProduct(slug) {
        try {
            this.showLoader();
            const response = await fetch(`${this.apiUrl}${slug}/`);

            if (!response.ok) {
                throw new Error(this.t('notFound'));
            }

            const data = await response.json();
            this.product = data;

            this.renderProduct();
            this.hideLoader();

        } catch (error) {
            window.logJSError('Product detail loading error: ' + error.message, {
                file: 'product-detail.js',
                slug: slug,
                apiUrl: this.apiUrl
            });
            this.showError(this.t('loadError'));
        }
    }

    renderProduct() {
        // Название продукта (уже переведённое с API)
        const titleElement = document.querySelector('.models_title');
        if (titleElement) {
            titleElement.textContent = this.product.title;
        }
        window.currentProductTitle = this.product.title;

        const heroImg = document.querySelector('.mxd-hero-06__car-image');
        if (heroImg && this.product.main_image_url) {
            heroImg.src = this.product.main_image_url;
            heroImg.alt = this.product.title;
        }

        this.renderFeatures();
        this.renderSpecifications();
        this.renderGallery();
        this.updateBreadcrumbs();
        this.generateSchemaMarkup();
    }

    renderFeatures() {
        const featuresContainer = document.querySelector('.car-specs-grid');
        if (!featuresContainer || !this.product.features) return;

        featuresContainer.innerHTML = '';

        const features = this.product.features
            .sort((a, b) => a.order - b.order)
            .slice(0, 8);

        features.forEach(feature => {
            const featureHTML = `
                <div class="car-spec-item">
                    <img src="${feature.icon.icon_url}" class="car-spec-icon" alt="${feature.icon.name}">
                    <div class="car-spec-content">
                        <div class="car-spec-label">${feature.name}</div>
                    </div>
                </div>
            `;
            featuresContainer.insertAdjacentHTML('beforeend', featureHTML);
        });
    }

    renderSpecifications() {
        const specsContainer = document.querySelector('.acardeon-cards_block');
        if (!specsContainer) return;

        specsContainer.innerHTML = '';

        if (!this.product.spec_groups || this.product.spec_groups.length === 0) {
            specsContainer.innerHTML = `<p style="padding: 20px; text-align: center; color: #888;">${this.t('noParams')}</p>`;
            return;
        }

        this.product.spec_groups.forEach((group, index) => {
            if (!group.parameters || group.parameters.length === 0) return;

            const isOpen = index === 0;
            const groupHTML = this.createAccordionCard(group, index, isOpen);
            specsContainer.insertAdjacentHTML('beforeend', groupHTML);
        });

        if (specsContainer.innerHTML === '') {
            specsContainer.innerHTML = `<p style="padding: 20px; text-align: center; color: #888;">${this.t('noParams')}</p>`;
        }
    }

    createAccordionCard(group, index, isOpen) {
        if (!group.parameters || group.parameters.length === 0) return '';

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

        galleryContainer.innerHTML = '';

        const images = this.product.gallery.sort((a, b) => a.order - b.order);

        if (images.length === 0) {
            this.addGallerySlide(galleryContainer, this.product.main_image_url, this.product.title);
        } else {
            images.forEach(img => {
                this.addGallerySlide(galleryContainer, img.image_url, this.product.title);
            });
        }

        const allImages = galleryContainer.querySelectorAll('img');
        if (allImages.length === 0) {
            this.initSwiper();
            return;
        }

        const imagePromises = Array.from(allImages).map(img => {
            return new Promise((resolve) => {
                if (img.complete && img.naturalHeight !== 0) {
                    resolve();
                } else {
                    img.addEventListener('load', resolve);
                    img.addEventListener('error', resolve);
                }
            });
        });

        Promise.all(imagePromises).then(() => {
            setTimeout(() => this.initSwiper(), 200);
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
        if (typeof Swiper === 'undefined') return;

        const existingSwiper = document.querySelector('.mxd-demo-swiper')?.swiper;
        if (existingSwiper) {
            existingSwiper.destroy(true, true);
        }

        const realSlides = document.querySelectorAll('.swiper-wrapper .swiper-slide').length;
        const minSlidesForLoop = 6;

        if (realSlides > 0 && realSlides < minSlidesForLoop) {
            const wrapper = document.querySelector('.swiper-wrapper');
            const slides = Array.from(wrapper.children);

            while (wrapper.children.length < minSlidesForLoop) {
                slides.forEach(slide => {
                    wrapper.appendChild(slide.cloneNode(true));
                });
            }
        }

        setTimeout(() => {
            const swiper = new Swiper('.mxd-demo-swiper', {
                breakpoints: {
                    320: { slidesPerView: 1, spaceBetween: 20 },
                    768: { slidesPerView: 2, spaceBetween: 30 },
                    1024: { slidesPerView: 3, spaceBetween: 30 },
                },
                loop: true,
                loopAdditionalSlides: 2,
                centeredSlides: true,
                initialSlide: 0,
                speed: 600,
                grabCursor: true,
                slidesPerGroup: 1,
                parallax: false,
                autoplay: false,
                keyboard: { enabled: true, onlyInViewport: true },
                navigation: {
                    nextEl: '.swiper-button-next',
                    prevEl: '.swiper-button-prev',
                },
                observer: true,
                observeParents: true,
                observeSlideChildren: true,
                watchOverflow: true,
                watchSlidesProgress: true,
                preventInteractionOnTransition: true,
                loopPreventsSlide: false,
                loopedSlides: null,
                on: {
                    init: function () {
                        setTimeout(() => {
                            this.update();
                            if (this.params.loop) {
                                this.slideToLoop(0, 0, false);
                            } else {
                                this.slideTo(0, 0, false);
                            }
                            this.update();
                        }, 150);

                        setTimeout(() => {
                            this.params.autoplay = {
                                delay: 4000,
                                disableOnInteraction: false,
                                pauseOnMouseEnter: true,
                            };
                            this.autoplay.start();
                        }, 1000);
                    },
                }
            });

            window.gallerySwiper = swiper;
        }, 400);
    }
    updateBreadcrumbs() {
        const breadcrumbLinks = document.querySelectorAll('.breadcrumb-ol li a');
        if (breadcrumbLinks.length < 3) return;

        const productLink = breadcrumbLinks[2];
        if (productLink) {
            productLink.textContent = this.product.title;
            productLink.href = 'javascript:void(0)';
        }

        const categoryLink = breadcrumbLinks[1];
        if (categoryLink) {
            const categoryName = this.t(`categories.${this.product.category}`) || 'Models';
            categoryLink.textContent = categoryName;
            categoryLink.href = `/#models`;
        }
    }
    generateSchemaMarkup() {
        const baseUrl = `${window.location.protocol}//${window.location.host}`;
        const currentUrl = window.location.href;

        // Product Schema
        const productSchema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": this.product.title,
            "image": this.product.main_image_url ? `${baseUrl}${this.product.main_image_url}` : [],
            "description": this.product.category_display || this.product.title,
            "brand": {
                "@type": "Brand",
                "name": "FAW"
            },
            "manufacturer": {
                "@type": "Organization",
                "name": "Van Universal Motors"
            },
            "category": this.product.category_display || "Commercial Vehicle"
        };

        // Добавляем галерею если есть
        if (this.product.gallery && this.product.gallery.length > 0) {
            productSchema.image = this.product.gallery.map(img => `${baseUrl}${img.image_url}`);
        }

        // BreadcrumbList Schema
        const breadcrumbSchema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": this.currentLanguage === 'uz' ? 'Bosh sahifa' : (this.currentLanguage === 'ru' ? 'Главная' : 'Home'),
                    "item": `${baseUrl}/`
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": this.currentLanguage === 'uz' ? 'Modellar' : (this.currentLanguage === 'ru' ? 'Модели' : 'Models'),
                    "item": `${baseUrl}/#models`
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": this.product.title,
                    "item": currentUrl
                }
            ]
        };

        // Вставляем разметку в DOM
        const productSchemaEl = document.getElementById('product-schema');
        const breadcrumbSchemaEl = document.getElementById('breadcrumb-schema');

        if (productSchemaEl) {
            productSchemaEl.textContent = JSON.stringify(productSchema, null, 2);
        }

        if (breadcrumbSchemaEl) {
            breadcrumbSchemaEl.textContent = JSON.stringify(breadcrumbSchema, null, 2);
        }
    }

    showLoader() {
        const loader = document.createElement('div');
        loader.id = 'product-loader';
        loader.className = 'page-loader';
        loader.innerHTML = `<div class="loader">${this.t('loading')}</div>`;
        document.body.appendChild(loader);
    }

    hideLoader() {
        const loader = document.getElementById('product-loader');
        if (loader) loader.remove();
    }

    showError(message) {
        this.hideLoader();
        const content = document.querySelector('.mxd-page-content');
        if (content) {
            content.innerHTML = `
                <div class="error-page">
                    <div class="grid-container">
                        <div class="error-content">
                            <h1>❌ ${this.t('error')}</h1>
                            <p>${message}</p>
                            <a href="/products/?category=samosval" class="btn btn-primary">
                                <span>${this.t('backToHome')}</span>
                            </a>
                        </div>
                    </div>
                </div>
            `;
        }
    }
}

// Инициализация
let productDetailInstance = null;

// Ждем полной загрузки страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProductDetail);
} else {
    // DOM уже загружен
    initProductDetail();
}

function initProductDetail() {
    // Дополнительная задержка для гарантии
    setTimeout(() => {
        productDetailInstance = new ProductDetail();
    }, 100);
}