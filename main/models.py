from django.db import models
from django.contrib.auth.models import User

# ============ ТОЛЬКО FAW.UZ ============

class News(models.Model):
    """Основная модель новости"""
    title = models.CharField("Заголовок", max_length=255)
    desc = models.TextField("Краткое описание", max_length=500)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    author_photo = models.ImageField("Фото автора", upload_to="authors/", blank=True, null=True)
    preview_image = models.ImageField("Главное фото", upload_to="news/previews/", blank=True, null=True)
    created_at = models.DateTimeField("Дата публикации", auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "[UZ] Новость"
        verbose_name_plural = "[UZ] Новости"


class NewsBlock(models.Model):
    """Гибкие блоки внутри новости"""
    BLOCK_TYPES = (
        ('text', 'Текст'),
        ('image', 'Изображение'),
        ('youtube', 'YouTube видео'),
        ('video', 'Видео файл'),
    )

    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="blocks", verbose_name="Новость")
    block_type = models.CharField("Тип блока", max_length=10, choices=BLOCK_TYPES)
    text = models.TextField("Текст", blank=True, null=True)
    image = models.ImageField("Фото", upload_to="news/images/", blank=True, null=True)
    youtube_url = models.URLField("YouTube ссылка", blank=True, null=True)
    video_file = models.FileField("Видео файл", upload_to="news/videos/", blank=True, null=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "[UZ] Блок новости"
        verbose_name_plural = "[UZ] Блоки новостей"

    def __str__(self):
        return f"{self.news.title} — {self.block_type}"


class ContactForm(models.Model):
    """Заявки с сайта faw.uz"""
    REGION_CHOICES = [
        ('Toshkent shahri', 'Toshkent shahri'),
        ('Andijon viloyati', 'Andijon viloyati'),
        ('Buxoro viloyati', 'Buxoro viloyati'),
        ('Fargʻona viloyati', 'Fargʻona viloyati'),
        ('Jizzax viloyati', 'Jizzax viloyati'),
        ('Xorazm viloyati', 'Xorazm viloyati'),
        ('Namangan viloyati', 'Namangan viloyati'),
        ('Navoiy viloyati', 'Navoiy viloyati'),
        ('Qashqadaryo viloyati', 'Qashqadaryo viloyati'),
        ('Samarqand viloyati', 'Samarqand viloyati'),
        ('Sirdaryo viloyati', 'Sirdaryo viloyati'),
        ('Surxondaryo viloyati', 'Surxondaryo viloyati'),
        ('Toshkent viloyati', 'Toshkent viloyati'),
        ('Qoraqalpogʻiston Respublikasi', 'Qoraqalpogʻiston Respublikasi'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_process', 'В процессе'),
        ('done', 'Обработана'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'Высокий'),
        ('medium', 'Средний'),
        ('low', 'Низкий'),
    ]

    name = models.CharField(max_length=255, verbose_name='Имя')
    region = models.CharField(max_length=100, choices=REGION_CHOICES, verbose_name='Регион')
    phone = models.CharField(max_length=50, verbose_name='Телефон')
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время отправки')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='Приоритет')
    manager = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='uz_contacts', verbose_name='Менеджер')
    is_processed = models.BooleanField(default=False, verbose_name='Просмотрено (устарело)')
    admin_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий администратора')

    class Meta:
        verbose_name = '[UZ] Заявка'
        verbose_name_plural = '[UZ] Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.phone} ({self.created_at.strftime('%d.%m.%Y')})"


class Vacancy(models.Model):
    """Вакансии компании"""
    title = models.CharField(max_length=255, verbose_name='Название вакансии')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='URL-имя')
    short_description = models.TextField(max_length=500, blank=True, verbose_name='Краткое описание')
    contact_info = models.TextField(
        verbose_name='Контактная информация',
        default='Присылайте своё резюме на <a href="https://hh.uz" target="_blank">hh.uz</a> или на корпоративную почту <a href="mailto:info@faw.uz">info@faw.uz</a>'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок отображения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Вакансия (UZ)'
        verbose_name_plural = 'Вакансии (UZ)'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title
    
    def get_applications_count(self):
        return self.applications.count()


class VacancyResponsibility(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='responsibilities', verbose_name='Вакансия')
    title = models.CharField(max_length=255, verbose_name='Заголовок', blank=True)
    text = models.TextField(verbose_name='Описание')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Обязанность'
        verbose_name_plural = 'Обязанности'
        ordering = ['order']

    def __str__(self):
        return self.title or self.text[:50]


class VacancyRequirement(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='requirements', verbose_name='Вакансия')
    text = models.CharField(max_length=500, verbose_name='Требование')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Требование'
        verbose_name_plural = 'Требования'
        ordering = ['order']

    def __str__(self):
        return self.text[:50]


class VacancyCondition(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='conditions', verbose_name='Вакансия')
    text = models.CharField(max_length=500, verbose_name='Условие')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Условие работы'
        verbose_name_plural = 'Условия работы'
        ordering = ['order']

    def __str__(self):
        return self.text[:50]


class VacancyIdealCandidate(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='ideal_candidates', verbose_name='Вакансия')
    text = models.CharField(max_length=500, verbose_name='Качество/Требование')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Портрет кандидата'
        verbose_name_plural = 'Портрет идеального кандидата'
        ordering = ['order']

    def __str__(self):
        return self.text[:50]


class JobApplication(models.Model):
    """Заявки на вакансии с резюме"""
    REGION_CHOICES = [
        ('Toshkent shahri', 'Toshkent shahri'),
        ('Andijon viloyati', 'Andijon viloyati'),
        ('Buxoro viloyati', 'Buxoro viloyati'),
        ('Fargʻona viloyati', 'Fargʻona viloyati'),
        ('Jizzax viloyati', 'Jizzax viloyati'),
        ('Xorazm viloyati', 'Xorazm viloyati'),
        ('Namangan viloyati', 'Namangan viloyati'),
        ('Navoiy viloyati', 'Navoiy viloyati'),
        ('Qashqadaryo viloyati', 'Qashqadaryo viloyati'),
        ('Samarqand viloyati', 'Samarqand viloyati'),
        ('Sirdaryo viloyati', 'Sirdaryo viloyati'),
        ('Surxondaryo viloyati', 'Surxondaryo viloyati'),
        ('Toshkent viloyati', 'Toshkent viloyati'),
        ('Qoraqalpogʻiston Respublikasi', 'Qoraqalpogʻiston Respublikasi'),
    ]
    
    vacancy = models.ForeignKey('Vacancy', on_delete=models.CASCADE, related_name='applications', verbose_name='Вакансия')
    region = models.CharField(max_length=100, choices=REGION_CHOICES, verbose_name='Регион')
    resume = models.FileField(upload_to='resumes/%Y/%m/', verbose_name='Резюме')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подачи')
    is_processed = models.BooleanField(default=False, verbose_name='Рассмотрено')
    admin_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий HR')
    applicant_name = models.CharField(max_length=255, blank=True, verbose_name='ФИО кандидата')
    applicant_phone = models.CharField(max_length=50, blank=True, verbose_name='Телефон')
    applicant_email = models.EmailField(blank=True, verbose_name='Email')

    class Meta:
        verbose_name = 'Заявка на вакансию (UZ)'
        verbose_name_plural = 'Заявки на вакансии (UZ)'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vacancy.title} - {self.region} ({self.created_at.strftime('%d.%m.%Y')})"
    
    def get_file_size(self):
        if self.resume:
            return round(self.resume.size / (1024 * 1024), 2)
        return 0


# ========== МОДЕЛИ ДЛЯ ПРОДУКТОВ FAW.UZ ==========

class FeatureIcon(models.Model):
    """Иконки для характеристик"""
    name = models.CharField("Название", max_length=100, unique=True)
    icon = models.FileField("Иконка SVG", upload_to="features/icons/")
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Иконка характеристики"
        verbose_name_plural = "Иконки характеристик"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class SpecificationCategory(models.Model):
    """Категории параметров (Двигатель, Комфорт, и т.д.)"""
    name = models.CharField("Название категории", max_length=100)
    slug = models.SlugField("URL", max_length=100, unique=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Категория параметров"
        verbose_name_plural = "Категории параметров"
        ordering = ['order', 'name']
    
    def __str__(self):
        return getattr(self, 'name', 'Без названия') or 'Без названия'


class Product(models.Model):
    """Модель грузовика FAW"""
    CATEGORY_CHOICES = [
        ('dump_truck', 'Самосвал'),
        ('tractor', 'Тягач'),
        ('chassis', 'Шасси'),
        ('van', 'Фургон'),
        ('special', 'Спецтехника'),
    ]
    
    title = models.CharField("Название модели", max_length=255)
    slug = models.SlugField("URL", max_length=255, unique=True)
    category = models.CharField("Категория", max_length=50, choices=CATEGORY_CHOICES)
    
    # ========== ЗАКОММЕНТИРОВАНО (можно раскомментировать при необходимости) ==========
    # short_description = models.TextField("Краткое описание", max_length=500, blank=True)
    # main_description = models.TextField("Основное описание", blank=True)
    # slogan = models.CharField("Слоган", max_length=255, blank=True)
    
    main_image = models.ImageField("Главное изображение", upload_to="products/main/")
    card_image = models.ImageField("Изображение для карточки", upload_to="products/cards/", blank=True, null=True)
    
    is_active = models.BooleanField("Активен", default=True)
    is_featured = models.BooleanField("Показывать на главной", default=False)
    order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Грузовик FAW"
        verbose_name_plural = "Грузовики FAW"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class ProductSpecificationGroup(models.Model):
    """Группа параметров для продукта (привязка категории к продукту)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='spec_groups', verbose_name='Продукт')
    category = models.ForeignKey(SpecificationCategory, on_delete=models.CASCADE, verbose_name='Категория')
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Группа параметров"
        verbose_name_plural = "Группы параметров"
        ordering = ['order', 'category__order']
        unique_together = ['product', 'category']
    
    def __str__(self):
        return f"{self.category.name}"


class ProductParameter(models.Model):
    """Конкретный параметр внутри группы"""
    group = models.ForeignKey(ProductSpecificationGroup, on_delete=models.CASCADE, related_name='parameters', verbose_name='Группа')
    text = models.CharField("Параметр", max_length=500, help_text='Например: Мощность двигателя: 300 л.с.')
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры"
        ordering = ['order']
    
    def __str__(self):
        return self.text[:50]


class ProductFeature(models.Model):
    """8 характеристик с иконками (для главной страницы)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features')
    icon = models.ForeignKey(FeatureIcon, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("Название", max_length=100)
    value = models.CharField("Значение", max_length=100, help_text='RU: Присутствует / EN: Available / UZ: Mavjud')
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Характеристика с иконкой"
        verbose_name_plural = "Характеристики с иконками"
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name}: {self.value}"


class ProductCardSpec(models.Model):
    """4 характеристики для карточки товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='card_specs')
    icon = models.ForeignKey(FeatureIcon, on_delete=models.SET_NULL, null=True, blank=True)
    value = models.CharField("Значение", max_length=100)
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Характеристика карточки"
        verbose_name_plural = "Характеристики карточки (4 шт)"
        ordering = ['order']
    
    def __str__(self):
        return self.value


class ProductGallery(models.Model):
    """Галерея продукта"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField("Изображение", upload_to="products/gallery/")
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Фото галереи"
        verbose_name_plural = "Галерея"
        ordering = ['order']
    
    def __str__(self):
        return f"Фото {self.order + 1}"