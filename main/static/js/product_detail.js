/**
 * FAW Product Detail - Production Version with Full Translation Support
 */

class ProductDetail {
    constructor() {
        this.productId = null;
        this.apiUrl = this.getApiUrl();
        this.product = null;
        this.init();
    }

    // Определяем API URL в зависимости от текущего языка
    getApiUrl() {
        // Получаем язык из Django
        const lang = document.documentElement.lang || 
                     window.LANGUAGE_CODE || 
                     this.getCookie('django_language') || 
                     'uz';
        
        return `/api/${lang}/products/`;
    }

    // Получаем cookie
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    async init() {
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
            console.error('Error loading product:', error);
            this.showError('Mahsulot yuklanmadi. Qayta urinib ko\'ring.');
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

        specsContainer.innerHTML = '';

        if (!this.product.spec_groups || this.product.spec_groups.length === 0) {
            specsContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: #888;">Parametrlar hali qo\'shilmagan</p>';
            return;
        }

        this.product.spec_groups.forEach((group, index) => {
            if (!group.parameters || group.parameters.length === 0) return;

            const isOpen = index === 0;
            const groupHTML = this.createAccordionCard(group, index, isOpen);
            specsContainer.insertAdjacentHTML('beforeend', groupHTML);
        });

        if (specsContainer.innerHTML === '') {
            specsContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: #888;">Parametrlar hali qo\'shilmagan</p>';
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
        const categoryNames = {
            'shatakchi': 'Shatakchi mashinalar',
            'samosval': 'Samosvallar',
            'maxsus': 'Maxsus texnika',
            'furgon': 'Avtofurgonlar',
            'shassi': 'Shassilar',
            'tiger_v': 'Tiger V',
            'tiger_vr': 'Tiger VR'
        };

        const breadcrumbLinks = document.querySelectorAll('.breadcrumb-ol li a');
        if (breadcrumbLinks.length < 3) return;

        const productLink = breadcrumbLinks[2];
        if (productLink) {
            productLink.textContent = this.product.title;
            productLink.href = 'javascript:void(0)';
        }

        const categoryLink = breadcrumbLinks[1];
        if (categoryLink) {
            const categoryName = this.product.category_display ||
                categoryNames[this.product.category] ||
                'Modellar';

            categoryLink.textContent = categoryName;
            categoryLink.href = `/#models`;
        }

        document.title = `${this.product.title} - FAW Trucks`;
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

// Инициализация
let productDetailInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    productDetailInstance = new ProductDetail();
});