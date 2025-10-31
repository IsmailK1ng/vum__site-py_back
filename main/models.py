from django.db import models
from django.contrib.auth.models import User

# ========== РЕГИОНЫ (общий выбор для всех форм) ==========
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


# ========== 01. КОНТЕНТ ==========

class News(models.Model):
    """Новости компании"""
    title = models.CharField("Заголовок", max_length=255)
    desc = models.TextField("Краткое описание", max_length=500)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    author_photo = models.ImageField("Фото автора", upload_to="authors/", blank=True, null=True)
    preview_image = models.ImageField("Главное фото", upload_to="news/previews/", blank=True, null=True)
    created_at = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        verbose_name = " - Новость"
        verbose_name_plural = "Контент - Новости"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class NewsBlock(models.Model):
    """Гибкие блоки внутри новости"""
    BLOCK_TYPES = [
        ('text', 'Текст'),
        ('image', 'Изображение'),
        ('youtube', 'YouTube видео'),
        ('video', 'Видео файл'),
    ]

    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="blocks", verbose_name="Новость")
    block_type = models.CharField("Тип блока", max_length=10, choices=BLOCK_TYPES)
    text = models.TextField("Текст", blank=True, null=True)
    image = models.ImageField("Фото", upload_to="news/images/", blank=True, null=True)
    youtube_url = models.URLField("YouTube ссылка", blank=True, null=True)
    video_file = models.FileField("Видео файл", upload_to="news/videos/", blank=True, null=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Блок новости"
        verbose_name_plural = "Блоки новостей"

    def __str__(self):
        return f"{self.news.title} — {self.block_type}"


class Product(models.Model):
    """Грузовики FAW"""
    CATEGORY_CHOICES = [
        ('shatakchi', 'Shatakchi mashinalar'),
        ('samosval', 'Samosvallar'),
        ('maxsus', 'Maxsus texnika'),
        ('furgon', 'Avtofurgonlar'),
        ('shassi', 'Shassilar'),
        ('tiger_v', 'Tiger V'),
        ('tiger_vr', 'Tiger VR'),
    ]
    
    title = models.CharField("Название модели", max_length=255)
    slug = models.SlugField("URL", max_length=255, unique=True)
    category = models.CharField("Категория", max_length=50, choices=CATEGORY_CHOICES)
    main_image = models.ImageField("Главное изображение", upload_to="products/main/")
    card_image = models.ImageField("Изображение для карточки", upload_to="products/cards/", blank=True, null=True)
    is_active = models.BooleanField("Активен", default=True)
    is_featured = models.BooleanField("Показывать на главной", default=False)
    order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Контент - Грузовик"
        verbose_name_plural = "Контент - Грузовики FAW"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class ProductParameter(models.Model):
    """Параметры грузовика"""
    CATEGORY_CHOICES = [
        ('main', 'Основные параметры'),
        ('engine', 'Двигатель'),
        ('weight', 'Весовые параметры'),
        ('transmission', 'Трансмиссия'),
        ('brakes', 'Система тормозов и шин'),
        ('comfort', 'Удобства'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='parameters', verbose_name='Продукт')
    category = models.CharField("Категория", max_length=50, choices=CATEGORY_CHOICES)
    text = models.CharField("Параметр", max_length=500)
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры машины"
        ordering = ['category', 'order']
    
    def __str__(self):
        return f"{self.get_category_display()}: {self.text[:50]}"


class ProductFeature(models.Model):
    """Характеристики с иконками"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features')
    icon = models.ForeignKey('FeatureIcon', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("Название", max_length=100)
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Характеристика"
        verbose_name_plural = "Характеристики с иконками"
        ordering = ['order']
    
    def __str__(self):
        return self.name


class ProductCardSpec(models.Model):
    """Характеристики для карточки"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='card_specs')
    icon = models.ForeignKey('FeatureIcon', on_delete=models.SET_NULL, null=True, blank=True)
    value = models.CharField("Значение", max_length=100)
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Характеристика карточки"
        verbose_name_plural = "Характеристики карточки"
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


class FeatureIcon(models.Model):
    """Иконки для характеристик"""
    name = models.CharField("Название", max_length=100, unique=True)
    icon = models.FileField("Иконка", upload_to="features/icons/")
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Контент - Иконка"
        verbose_name_plural = "Контент - Иконки"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class BecomeADealerPage(models.Model):
    """Страница 'Стать дилером' (Singleton)"""
    title = models.CharField("Заголовок", max_length=255, default="Qanday qilib diler bo'lish mumkin")
    intro_text = models.TextField("Вводный текст")
    subtitle = models.CharField("Подзаголовок списка", max_length=255, default="Potensial diler kompaniyasining minimal tarkibi:")
    important_note = models.TextField("Важная заметка")
    contact_phone = models.CharField("Телефон", max_length=50, default="+998 71 234-56-78")
    contact_email = models.EmailField("Email", default="info@faw.uz")
    contact_address = models.TextField("Адрес", default="Toshkent, Abdulla Kaxxar ko'chasi 2А")
    
    class Meta:
        verbose_name = "Контент - Страница 'Стать дилером'"
        verbose_name_plural = "Контент - Страница 'Стать дилером'"
    
    def __str__(self):
        return "Контент страницы 'Стать дилером'"
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class DealerRequirement(models.Model):
    """Требования к дилерам"""
    page = models.ForeignKey(BecomeADealerPage, on_delete=models.CASCADE, related_name='requirements')
    text = models.CharField("Требование", max_length=500)
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Требование"
        verbose_name_plural = "Требования"
        ordering = ['order']
    
    def __str__(self):
        return self.text[:50]


# ========== 02. ЗАЯВКИ ==========

class ContactForm(models.Model):
    """Общие заявки с сайта"""
    name = models.CharField("Имя", max_length=255)
    region = models.CharField("Регион", max_length=100, choices=REGION_CHOICES)
    phone = models.CharField("Телефон", max_length=50)
    message = models.TextField("Сообщение")
    created_at = models.DateTimeField("Дата", auto_now_add=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField("Приоритет", max_length=10, choices=PRIORITY_CHOICES, default='medium')
    manager = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='uz_contacts', verbose_name='Менеджер')
    admin_comment = models.TextField("Комментарий", blank=True, null=True)

    class Meta:
        verbose_name = "Заявки - Общая заявка"
        verbose_name_plural = "Заявки - Общие заявки"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.phone} ({self.created_at.strftime('%d.%m.%Y')})"


class BecomeADealerApplication(models.Model):
    """Заявки на дилерство"""
    name = models.CharField("ФИО", max_length=255)
    region = models.CharField("Регион", max_length=100, choices=REGION_CHOICES)
    phone = models.CharField("Телефон", max_length=50)
    message = models.TextField("Сообщение")
    company_name = models.CharField("Компания", max_length=255, blank=True)
    experience_years = models.PositiveIntegerField("Опыт (лет)", blank=True, null=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField("Приоритет", max_length=10, choices=PRIORITY_CHOICES, default='medium')
    manager = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='dealer_applications', verbose_name='Менеджер')
    admin_comment = models.TextField("Комментарий", blank=True, null=True)
    created_at = models.DateTimeField("Дата", auto_now_add=True)
    
    class Meta:
        verbose_name = " - Заявка на дилерство"
        verbose_name_plural = "Заявки - Заявки на дилерство"
        ordering = ['-created_at']
    
    def __str__(self):
        company = f" ({self.company_name})" if self.company_name else ""
        return f"{self.name}{company} - {self.region}"


class JobApplication(models.Model):
    """Заявки на вакансии"""
    vacancy = models.ForeignKey('Vacancy', on_delete=models.CASCADE, related_name='applications', verbose_name='Вакансия')
    region = models.CharField("Регион", max_length=100, choices=REGION_CHOICES)
    resume = models.FileField("Резюме", upload_to='resumes/%Y/%m/')
    applicant_name = models.CharField("ФИО", max_length=255, blank=True)
    applicant_phone = models.CharField("Телефон", max_length=50, blank=True)
    applicant_email = models.EmailField("Email", blank=True)
    created_at = models.DateTimeField("Дата", auto_now_add=True)
    is_processed = models.BooleanField("Рассмотрено", default=False)
    admin_comment = models.TextField("Комментарий HR", blank=True, null=True)

    class Meta:
        verbose_name = "Заявки - Заявка на вакансию"
        verbose_name_plural = "Заявки - Заявки на вакансии"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vacancy.title} - {self.region}"
    
    def get_file_size(self):
        return round(self.resume.size / (1024 * 1024), 2) if self.resume else 0


# ========== 03. ДИЛЕРЫ ==========

class DealerService(models.Model):
    """Услуги дилеров"""
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField("URL", max_length=100, unique=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)
    
    class Meta:
        verbose_name = "Дилеры - Услуга"
        verbose_name_plural = "Дилеры - Услуги дилеров"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Dealer(models.Model):
    """Дилеры FAW"""
    name = models.CharField("Название", max_length=255)
    city = models.CharField("Город", max_length=100)
    address = models.TextField("Адрес")
    latitude = models.DecimalField("Широта", max_digits=9, decimal_places=6, help_text="Пример: 41.311151")
    longitude = models.DecimalField("Долгота", max_digits=9, decimal_places=6, help_text="Пример: 69.279737")
    phone = models.CharField("Телефон", max_length=50)
    email = models.EmailField("Email")
    website = models.URLField("Сайт", blank=True, null=True)
    working_hours = models.TextField("Рабочее время", help_text="Используйте <br> для переноса")
    manager = models.CharField("Менеджер", max_length=100, blank=True, null=True)
    services = models.ManyToManyField(DealerService, verbose_name="Услуги", related_name='dealers')
    logo = models.ImageField("Логотип", upload_to="dealers/logos/", blank=True, null=True)
    is_active = models.BooleanField("Активен", default=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    
    class Meta:
        verbose_name = "Дилеры - Дилер"
        verbose_name_plural = "Дилеры - Дилеры"
        ordering = ['order', 'city', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.city})"


# ========== 04. ВАКАНСИИ ==========

class Vacancy(models.Model):
    """Вакансии компании"""
    title = models.CharField("Название", max_length=255)
    slug = models.SlugField("URL", max_length=255, unique=True)
    short_description = models.TextField("Описание", max_length=500, blank=True)
    contact_info = models.TextField("Контакты", default='Присылайте резюме на info@faw.uz')
    is_active = models.BooleanField("Активна", default=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Вакансии - Вакансия"
        verbose_name_plural = "Вакансии - Вакансии"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title
    
    def get_applications_count(self):
        return self.applications.count()


class VacancyResponsibility(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='responsibilities')
    title = models.CharField("Заголовок", max_length=255, blank=True)
    text = models.TextField("Описание")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Обязанность"
        verbose_name_plural = "Обязанности"
        ordering = ['order']

    def __str__(self):
        return self.title or self.text[:50]


class VacancyRequirement(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='requirements')
    text = models.CharField("Требование", max_length=500)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Требование"
        verbose_name_plural = "Требования"
        ordering = ['order']

    def __str__(self):
        return self.text[:50]


class VacancyCondition(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='conditions')
    text = models.CharField("Условие", max_length=500)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Условие"
        verbose_name_plural = "Условия"
        ordering = ['order']

    def __str__(self):
        return self.text[:50]


class VacancyIdealCandidate(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='ideal_candidates')
    text = models.CharField("Качество", max_length=500)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Портрет кандидата"
        verbose_name_plural = "Портрет кандидата"
        ordering = ['order']

    def __str__(self):
        return self.text[:50]
# ========== 05. СТАТИЧНЫЕ СТРАНИЦЫ ==========

