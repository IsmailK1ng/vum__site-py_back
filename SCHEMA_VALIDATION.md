# Инструкция по проверке микро-разметки Schema.org

## Что было внедрено

На сайте VUM внедрена микро-разметка Schema.org согласно документации Google:

### 1. **NewsArticle** - для страниц новостей
- **Файл:** `main/templates/main/news_detail.html`
- **Тип разметки:** NewsArticle
- **Включает:**
  - Заголовок, описание, изображение
  - Дату публикации и обновления
  - Информацию об авторе
  - Информацию о издателе (Organization)
- **Документация:** https://developers.google.com/search/docs/appearance/structured-data/article

### 2. **BreadcrumbList** - хлебные крошки
- **Файлы:**
  - `main/templates/main/news_detail.html` (статические)
  - `main/templates/main/product_detail.html` (динамические через JS)
- **Тип разметки:** BreadcrumbList
- **Включает:** иерархию навигации по сайту
- **Документация:** https://developers.google.com/search/docs/appearance/structured-data/breadcrumb

### 3. **Product** - для страниц продуктов
- **Файлы:**
  - `main/templates/main/product_detail.html` (контейнер)
  - `main/static/js/product_detail.js` (генерация через JS)
- **Тип разметки:** Product
- **Включает:**
  - Название продукта
  - Изображения (главное + галерея)
  - Бренд (FAW)
  - Производитель (Van Universal Motors)
  - Категория
- **Примечание:** Разметка генерируется динамически через JavaScript при загрузке страницы продукта

### 4. **Organization** - информация о компании
- **Файл:** `main/templates/main/index.html`
- **Тип разметки:** Organization
- **Включает:**
  - Название компании (Van Universal Motors / VUM)
  - Логотип
  - Описание
  - Адрес
  - Контактная информация
- **Документация:** https://developers.google.com/search/docs/appearance/structured-data/logo

### 5. **WebSite** - информация о сайте
- **Файл:** `main/templates/main/index.html`
- **Тип разметки:** WebSite
- **Включает:**
  - Название сайта
  - URL
  - Издатель

### 6. **ItemList** - каталог продуктов
- **Файлы:**
  - `main/templates/main/products.html` (контейнер + хлебные крошки)
  - `main/static/js/production.js` (генерация через JS)
- **Тип разметки:** ItemList с вложенными Product
- **Включает:**
  - Список продуктов в категории (до 20 шт)
  - Информация о каждом продукте (название, изображение, URL, бренд)
  - Хлебные крошки для навигации
- **Примечание:** Разметка генерируется динамически после загрузки продуктов из API
- **Документация:** https://developers.google.com/search/docs/appearance/structured-data/carousel

### 7. **ItemList (News)** - каталог новостей
- **Файл:** `main/templates/main/news.html`
- **Тип разметки:** ItemList с вложенными NewsArticle
- **Включает:**
  - Список всех новостей
  - Для каждой новости: заголовок, описание, изображение, дата, URL
  - Хлебные крошки
- **Документация:** https://developers.google.com/search/docs/appearance/structured-data/article

### 8. **JobPosting** - вакансии
- **Файл:** `main/templates/main/jobs.html`
- **Тип разметки:** ItemList с вложенными JobPosting
- **Включает:**
  - Список вакансий
  - Название, описание, дата публикации
  - Информация о работодателе (VUM)
  - Местоположение (Узбекистан)
  - Хлебные крошки
- **Документация:** https://developers.google.com/search/docs/appearance/structured-data/job-posting

### 9. **LocalBusiness** - дилеры
- **Файл:** `main/templates/main/dealers.html`
- **Тип разметки:** ItemList с вложенными LocalBusiness
- **Включает:**
  - Список дилеров по всему Узбекистану
  - Название, адрес, телефон, email
  - Геокоординаты
  - Логотип (если есть)
  - Хлебные крошки
- **Документация:** https://developers.google.com/search/docs/appearance/structured-data/local-business

### 10. **AboutPage** - о компании
- **Файл:** `main/templates/main/about.html`
- **Тип разметки:** AboutPage с Organization
- **Включает:**
  - Описание компании VUM
  - Полная информация об организации
  - Адрес, контакты
  - Хлебные крошки
- **Документация:** https://schema.org/AboutPage

### 11. **ContactPage** - контакты
- **Файл:** `main/templates/main/contact.html`
- **Тип разметки:** ContactPage с Organization
- **Включает:**
  - Контактная информация VUM
  - Адрес, телефон, email
  - Доступные языки (uz, ru, en)
  - Хлебные крошки
- **Документация:** https://schema.org/ContactPage

## Как проверить разметку

### Метод 1: Google Rich Results Test (рекомендуется)

1. Перейдите на https://search.google.com/test/rich-results
2. Введите URL страницы для проверки:
   - **Главная страница:** `https://your-domain.com/`
   - **Каталог продуктов:** `https://your-domain.com/products/?category=samosval`
   - **Страница продукта:** `https://your-domain.com/products/[slug]/`
   - **Каталог новостей:** `https://your-domain.com/news/`
   - **Страница новости:** `https://your-domain.com/news/[slug]/`
   - **Вакансии:** `https://your-domain.com/jobs/`
   - **Дилеры:** `https://your-domain.com/dealers/`
   - **О компании:** `https://your-domain.com/about/`
   - **Контакты:** `https://your-domain.com/contact/`
3. Нажмите "Test URL"
4. Проверьте результаты - должно быть "Valid" без ошибок

### Метод 2: Schema.org Validator

1. Перейдите на https://validator.schema.org/
2. Введите URL страницы
3. Проверьте, что разметка валидна

### Метод 3: Просмотр в браузере

1. Откройте страницу в браузере
2. Нажмите `Ctrl+U` (просмотр исходного кода)
3. Найдите блоки `<script type="application/ld+json">`
4. Скопируйте JSON и проверьте на https://jsonlint.com/

### Метод 4: Google Search Console (после индексации)

1. Войдите в Google Search Console
2. Перейдите в раздел "Улучшения" → "Structured Data"
3. Просмотрите статистику по типам разметки
4. Исправьте ошибки, если они есть

## Что проверять

### ✅ Чек-лист для проверки

**Общие проверки:**
- [ ] Все JSON-LD блоки валидны (нет синтаксических ошибок)
- [ ] Все обязательные поля заполнены
- [ ] URL-адреса абсолютные (начинаются с http:// или https://)
- [ ] Даты в правильном ISO формате

**Страницы новостей (NewsArticle):**
- [ ] Заголовок новости отображается
- [ ] Дата публикации корректна
- [ ] Изображение загружается
- [ ] Автор указан
- [ ] Издатель (Van Universal Motors) указан
- [ ] Хлебные крошки построены правильно

**Каталог продуктов (ItemList):**
- [ ] Список продуктов отображается
- [ ] До 20 продуктов в разметке
- [ ] Каждый продукт имеет название, изображение, URL
- [ ] Хлебные крошки корректны
- [ ] Категория отображается правильно

**Каталог новостей (ItemList with NewsArticle):**
- [ ] Список новостей отображается
- [ ] Каждая новость имеет заголовок, описание, дату
- [ ] Изображения загружаются
- [ ] Хлебные крошки корректны

**Вакансии (JobPosting):**
- [ ] Список вакансий отображается
- [ ] Название и описание вакансий корректны
- [ ] Работодатель VUM указан
- [ ] Местоположение указано

**Дилеры (LocalBusiness):**
- [ ] Список дилеров отображается
- [ ] Адреса и контакты корректны
- [ ] Геокоординаты указаны
- [ ] Телефоны и email корректны

**О компании (AboutPage):**
- [ ] Информация об организации VUM
- [ ] Адрес и контакты корректны
- [ ] Хлебные крошки построены правильно

**Контакты (ContactPage):**
- [ ] Контактная информация отображается
- [ ] Доступные языки указаны
- [ ] Адрес, телефон, email корректны
- [ ] Хлебные крошки построены правильно

**Страницы продуктов (Product):**
- [ ] Название продукта отображается
- [ ] Изображения загружаются
- [ ] Бренд FAW указан
- [ ] Производитель VUM указан
- [ ] Хлебные крошки генерируются динамически

**Главная страница (Organization + WebSite):**
- [ ] Название компании корректное
- [ ] Логотип загружается
- [ ] Адрес указан правильно
- [ ] Телефон и email корректны

## Типичные ошибки и решения

### Ошибка: "Missing required field"
**Решение:** Убедитесь, что все обязательные поля заполнены в шаблонах

### Ошибка: "Invalid URL"
**Решение:** Проверьте, что все URL абсолютные (используется `request.scheme` и `request.get_host`)

### Ошибка: "Invalid date format"
**Решение:** Убедитесь, что используется фильтр Django `|date:'c'` для ISO формата

### Ошибка: "Image not found"
**Решение:** Проверьте, что изображения доступны по указанным URL

## Дополнительные возможности (опционально)

Если в будущем понадобятся дополнительные типы разметки:

### FAQPage (пока не реализовано)
Если на сайте появится раздел FAQ, можно добавить FAQPage разметку:
https://developers.google.com/search/docs/appearance/structured-data/faqpage

### Review (пока не реализовано)
Если появятся отзывы клиентов, можно добавить Review разметку:
https://developers.google.com/search/docs/appearance/structured-data/review-snippet

## Мониторинг после внедрения

1. Подождите 1-2 недели после внедрения
2. Проверьте Google Search Console → "Улучшения"
3. Отслеживайте появление расширенных сниппетов в поиске Google
4. При необходимости внесите корректировки

При возникновении вопросов или ошибок:
- Провереям документацию Google: https://developers.google.com/search/docs/appearance/structured-data/search-gallery
- Используйте валидатор: https://validator.schema.org/
