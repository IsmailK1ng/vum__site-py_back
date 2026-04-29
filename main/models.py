from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from unidecode import unidecode
from ckeditor.fields import RichTextField  
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta, time as datetime_time
from django.core.cache import cache 
# ========== ОБЩИЕ CHOICES ==========

REGION_CHOICES = [
    ('tashkent_city',    'Toshkent shahri'),
    ('andijan',          'Andijon viloyati'),
    ('bukhara',          'Buxoro viloyati'),
    ('fergana',          "Farg'ona viloyati"),
    ('jizzakh',          'Jizzax viloyati'),
    ('khorezm',          'Xorazm viloyati'),
    ('namangan',         'Namangan viloyati'),
    ('navoi',            'Navoiy viloyati'),
    ('kashkadarya',      'Qashqadaryo viloyati'),
    ('samarkand',        'Samarqand viloyati'),
    ('syrdarya',         'Sirdaryo viloyati'),
    ('surkhandarya',     'Surxondaryo viloyati'),
    ('tashkent_region',  'Toshkent viloyati'),
    ('karakalpakstan',   "Qoraqalpog'iston Respublikasi"),
]

REGION_LABELS = {
    'tashkent_city':   {'ru': 'г. Ташкент',                   'uz': 'Toshkent shahri',             'en': 'Tashkent city'},
    'andijan':         {'ru': 'Андижанская область',           'uz': 'Andijon viloyati',            'en': 'Andijan region'},
    'bukhara':         {'ru': 'Бухарская область',             'uz': 'Buxoro viloyati',             'en': 'Bukhara region'},
    'fergana':         {'ru': 'Ферганская область',            'uz': "Farg'ona viloyati",           'en': 'Fergana region'},
    'jizzakh':         {'ru': 'Джизакская область',            'uz': 'Jizzax viloyati',             'en': 'Jizzakh region'},
    'khorezm':         {'ru': 'Хорезмская область',            'uz': 'Xorazm viloyati',             'en': 'Khorezm region'},
    'namangan':        {'ru': 'Наманганская область',          'uz': 'Namangan viloyati',           'en': 'Namangan region'},
    'navoi':           {'ru': 'Навоийская область',            'uz': 'Navoiy viloyati',             'en': 'Navoi region'},
    'kashkadarya':     {'ru': 'Кашкадарьинская область',       'uz': 'Qashqadaryo viloyati',        'en': 'Kashkadarya region'},
    'samarkand':       {'ru': 'Самаркандская область',         'uz': 'Samarqand viloyati',          'en': 'Samarkand region'},
    'syrdarya':        {'ru': 'Сырдарьинская область',         'uz': 'Sirdaryo viloyati',           'en': 'Syrdarya region'},
    'surkhandarya':    {'ru': 'Сурхандарьинская область',      'uz': 'Surxondaryo viloyati',        'en': 'Surkhandarya region'},
    'tashkent_region': {'ru': 'Ташкентская область',           'uz': 'Toshkent viloyati',           'en': 'Tashkent region'},
    'karakalpakstan':  {'ru': 'Республика Каракалпакстан',     'uz': "Qoraqalpog'iston Respublikasi", 'en': 'Republic of Karakalpakstan'},
}

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

# ========== 01. КОНТЕНТ - НОВОСТИ ==========

class News(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    desc = models.TextField("Краткое описание для карточки", max_length=200, help_text="Отображается в превью новости")
    slug = models.SlugField("URL", max_length=255, unique=True, blank=True, help_text="Генерируется автоматически из заголовка")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    author_photo = models.ImageField("Фото автора", upload_to="authors/", blank=True, null=True)
    preview_image = models.ImageField("Главное фото", upload_to="news/previews/", blank=True, null=True)
    is_active = models.BooleanField("Активна", default=True, help_text="Показывать новость на сайте")
    order = models.PositiveIntegerField("Порядок", default=0, help_text="Чем больше число, тем выше в списке")
    
    created_at = models.DateField("Дата публикации", help_text="Введите дату публикации вручную")
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = " - Новость"
        verbose_name_plural = "Контент - Новости"
        ordering = ['-order', '-created_at']

    def __str__(self):
        return f"{self.created_at.strftime('%d.%m.%Y')} — {self.title[:50]}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            title_for_slug = (
                getattr(self, 'title_uz', None) or 
                getattr(self, 'title_ru', None) or 
                self.title or 
                "novost"
            )
            
            base_slug = slugify(unidecode(title_for_slug))
            slug = base_slug
            counter = 1
            
            while News.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)

class NewsBlock(models.Model):
    BLOCK_TYPES = [
        ('text', 'Текст'),
        ('image', 'Изображение'),
        ('youtube', 'YouTube видео'),
        ('video', 'Видео файл'),
    ]

    news = models.ForeignKey(
        News, 
        on_delete=models.CASCADE, 
        related_name="blocks", 
        verbose_name="Новость"
    )
    block_type = models.CharField("Тип блока", max_length=10, choices=BLOCK_TYPES)
    
    title = models.CharField(
        "Заголовок (необязательно)", 
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Заголовок H3 перед текстовым блоком"
    )
    
    text = RichTextField("Текст", blank=True, null=True, config_name='default')
    image = models.ImageField("Фото", upload_to="news/images/", blank=True, null=True)
    youtube_url = models.URLField("YouTube ссылка", blank=True, null=True)
    video_file = models.FileField("Видео файл", upload_to="news/videos/", blank=True, null=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Блок новости"
        verbose_name_plural = "Блоки новостей"

    def __str__(self):
        type_display = self.get_block_type_display()
        if self.title:
            return f"{self.news.title[:30]} — {type_display}: {self.title[:30]}"
        return f"{self.news.title[:30]} — {type_display}"

# ========== 02. КОНТЕНТ - ПРОДУКТЫ ==========

class FeatureIcon(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    icon = models.FileField("Иконка", upload_to="features/icons/")
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Контент - Иконка"
        verbose_name_plural = "Контент - Иконки"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('samosval', 'Samosvallar'),
        ('maxsus', 'Maxsus texnika'),
        ('furgon', 'Avtofurgonlar'),
        ('shassi', 'Shassilar'),
        ('tiger_v', 'Tiger V'),
        ('tiger_vh', 'Tiger VH'),
        ('tiger_vr', 'Tiger VR'),
    ]
    
    title = models.CharField("Название модели", max_length=255)
    slug = models.SlugField("URL", max_length=255, unique=True)
    category = models.CharField("Категория", max_length=50, choices=CATEGORY_CHOICES)
    categories = models.CharField(
        "Категории (множественный выбор)",
        max_length=255,
        blank=True,
        null=True,
        help_text="Выберите категории через запятую. Например: samosval,maxsus"
    )
    price = models.DecimalField(
        "Цена (UZS)",
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Цена в узбекских сумах для отображения диапазона цен в категориях"
    )
    price_is_from = models.BooleanField(
        "Цена 'от'",
        default=False,
        help_text="Если включено, перед ценой будет отображаться слово 'от'"
    )
    main_image = models.ImageField("Главное изображение", upload_to="products/main/")
    card_image = models.ImageField(
        "Изображение для карточки",
        upload_to="products/cards/",
        blank=True,
        null=True
    )
    
    # ========== НОВЫЕ ПОЛЯ ДЛЯ СЛАЙДЕРА ==========
    slider_image = models.ImageField(
        "Изображение для слайдера",
        upload_to="products/slider/",
        blank=True,
        null=True,
        help_text="Рекомендуемый размер: 420x210px. Если не указано, используется main_image"
    )
    slider_year = models.CharField(
        "Год для слайдера",
        max_length=4,
        default="2025",
        help_text="Отображается в слайдере"
    )
    slider_price = models.CharField(
        "Цена для слайдера",
        max_length=100,
        blank=True,
        null=True,
        help_text="Например: '434 000 000 sum'"
    )
    slider_power = models.CharField(
        "Мощность для слайдера",
        max_length=50,
        blank=True,
        null=True,
        help_text="Например: '185 o.k.'"
    )
    slider_fuel_consumption = models.CharField(
        "Расход топлива для слайдера",
        max_length=50,
        blank=True,
        null=True,
        help_text="Например: '17 L/100km'"
    )
    slider_order = models.PositiveIntegerField(
        "Порядок в слайдере",
        default=0,
        help_text="Чем больше число, тем раньше появится в слайдере"
    )
    # ========================================
    
    is_active = models.BooleanField("Активен", default=True)
    is_featured = models.BooleanField(
        "Показывать на главной", 
        default=False,
        help_text="Продукт будет добавлен в главный слайдер"
    )
    order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Контент - Грузовик"
        verbose_name_plural = "Контент - Грузовики FAW"
        ordering = ['order', 'title']

    def __str__(self):
        return f"{self.get_category_display()} — {self.title}"
    
    def get_slider_data(self):
        return {
            'year': self.slider_year,
            'title': self.title,
            'price': self.slider_price or 'Запросить цену',
            'power': self.slider_power or '—',
            'mpg': self.slider_fuel_consumption or '—',
            'image': (self.slider_image or self.main_image).url if (self.slider_image or self.main_image) else None,
            'link': f'/products/{self.slug}/',
        }
    
    def get_all_categories(self):
        categories = [self.category]
        
        if self.categories:
            additional = [cat.strip() for cat in self.categories.split(',') if cat.strip()]
            categories.extend(additional)
        
        return list(dict.fromkeys(categories))
        
    def get_all_categories_display(self):
        category_names = []
        for cat_slug in self.get_all_categories():
            for slug, name in self.CATEGORY_CHOICES:
                if slug == cat_slug:
                    category_names.append(name)
                    break
        return category_names

class ProductParameter(models.Model):
    CATEGORY_CHOICES = [
        ('main', _('Основные параметры')),
        ('engine', _('Двигатель')),
        ('weight', _('Весовые параметры')),
        ('transmission', _('Трансмиссия')),
        ('brakes', _('Система тормозов и шин')),
        ('comfort', _('Удобства')),
        ('superstructure', _('Надстройка')),
        ('cabin', _('Кабина')),
        ('additional', _('Дополнительные параметры')),
    ]
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='parameters', 
        verbose_name='Продукт'
    )
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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features')
    icon = models.ForeignKey(FeatureIcon, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("Название", max_length=100)
    order = models.PositiveIntegerField("Порядок", default=0, blank=True)
    
    class Meta:
        verbose_name = "Характеристика"
        verbose_name_plural = "Характеристики с иконками"
        ordering = ['order']
    
    def save(self, *args, **kwargs):
        if not self.order and self.product_id:
            max_order = ProductFeature.objects.filter(
                product=self.product
            ).exclude(pk=self.pk).aggregate(
                models.Max('order')
            )['order__max'] or 0
            self.order = max_order + 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class ProductCardSpec(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='card_specs')
    icon = models.ForeignKey(FeatureIcon, on_delete=models.SET_NULL, null=True, blank=True)
    value = models.CharField("Значение", max_length=100)
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Характеристика карточки"
        verbose_name_plural = "Характеристики карточки"
        ordering = ['order']
    
    def __str__(self):
        return self.value

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField("Изображение", upload_to="products/gallery/")
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Фото галереи"
        verbose_name_plural = "Галерея"
        ordering = ['order']
    
    def __str__(self):
        return f"Фото {self.order + 1}"

# ========== 03. КОНТЕНТ - ДИЛЕРЫ ==========

class BecomeADealerPage(models.Model):
    title = models.CharField(
        "Заголовок", 
        max_length=255, 
        default="Qanday qilib diler bo'lish mumkin"
    )
    intro_text = models.TextField("Вводный текст")
    subtitle = models.CharField(
        "Подзаголовок списка", 
        max_length=255, 
        default="Potensial diler kompaniyasining minimal tarkibi:"
    )
    important_note = models.TextField("Важная заметка")
    contact_phone = models.CharField("Телефон", max_length=50, default="+998 71 234-56-78")
    contact_email = models.EmailField("Email", default="info@faw.uz")
    contact_address = models.TextField(
        "Адрес", 
        default="Toshkent, Abdulla Kaxxar ko'chasi 2А"
    )
    
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
    page = models.ForeignKey(
        BecomeADealerPage, 
        on_delete=models.CASCADE, 
        related_name='requirements'
    )
    text = models.CharField("Требование", max_length=500)
    order = models.PositiveIntegerField("Порядок", default=0)
    
    class Meta:
        verbose_name = "Требование"
        verbose_name_plural = "Требования"
        ordering = ['order']
    
    def __str__(self):
        return self.text[:50]

class DealerService(models.Model):
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
    name = models.CharField("Название", max_length=255)
    city = models.CharField("Город", max_length=100)
    address = models.TextField("Адрес")
    latitude = models.DecimalField(
        "Широта", 
        max_digits=9, 
        decimal_places=6, 
        help_text="Пример: 41.311151"
    )
    longitude = models.DecimalField(
        "Долгота", 
        max_digits=9, 
        decimal_places=6, 
        help_text="Пример: 69.279737"
    )
    phone = models.CharField("Телефон", max_length=50)
    email = models.EmailField("Email")
    website = models.URLField("Сайт", blank=True, null=True)
    working_hours = models.TextField(
        "Рабочее время", 
        help_text="Используйте <br> для переноса"
    )
    manager = models.CharField("Менеджер", max_length=100, blank=True, null=True)
    services = models.ManyToManyField(
        DealerService, 
        verbose_name="Услуги", 
        related_name='dealers'
    )
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

# ========== 04. ЗАЯВКИ ==========

class ContactForm(models.Model):
    name = models.CharField("Имя", max_length=255)
    region = models.CharField("Регион", max_length=100, choices=REGION_CHOICES)
    phone = models.CharField("Телефон", max_length=50)
    
    product = models.CharField(
        "Модель техники", 
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Какую модель автомобиля интересует клиента"
    )
    
    
    referer = models.CharField(
        "Referer (откуда пришёл)",
        max_length=500,
        blank=True,
        null=True,
        help_text="URL страницы, с которой отправлена заявка"
    )
    
    utm_data = models.TextField(
        "UTM метки",
        blank=True,
        null=True,
        help_text="UTM метки в JSON формате"
    )

    visitor_uid = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="amoCRM Visitor UID"
    )
    
    created_at = models.DateTimeField("Дата", auto_now_add=True)
    message = models.TextField("Сообщение", blank=True, default='')
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField("Приоритет", max_length=10, choices=PRIORITY_CHOICES, default='medium')
    manager = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='uz_contacts', 
        verbose_name='Менеджер'
    )
    admin_comment = models.TextField("Комментарий", blank=True, null=True)
    
    amocrm_status = models.CharField(
        "Статус amoCRM",
        max_length=20,
        choices=[
            ('pending', 'Ожидает отправки'),
            ('sent', 'Успешно отправлено'),
            ('failed', 'Ошибка отправки'),
        ],
        default='pending',
        db_index=True,
        help_text="Статус отправки в amoCRM"
    )
    
    amocrm_lead_id = models.CharField(
        "ID лида в amoCRM",
        max_length=50,
        blank=True,
        null=True,
        help_text="ID лида после успешной отправки"
    )
    
    amocrm_sent_at = models.DateTimeField(
        "Дата отправки в amoCRM",
        blank=True,
        null=True
    )
    
    amocrm_error = models.TextField(
        "Ошибка amoCRM",
        blank=True,
        null=True,
        help_text="Текст последней ошибки при отправке"
    )
    
    class Meta:
        verbose_name = "Заявки - Общая заявка"
        verbose_name_plural = "Заявки - Общие заявки"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.phone} ({self.created_at.strftime('%d.%m.%Y')})"

class BecomeADealerApplication(models.Model):
    name = models.CharField("ФИО", max_length=255)
    region = models.CharField("Регион", max_length=100, choices=REGION_CHOICES)
    phone = models.CharField("Телефон", max_length=50)
    message = models.TextField("Сообщение")
    company_name = models.CharField("Компания", max_length=255, blank=True)
    experience_years = models.PositiveIntegerField("Опыт (лет)", blank=True, null=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField("Приоритет", max_length=10, choices=PRIORITY_CHOICES, default='medium')
    manager = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='dealer_applications', 
        verbose_name='Менеджер'
    )
    admin_comment = models.TextField("Комментарий", blank=True, null=True)
    created_at = models.DateTimeField("Дата", auto_now_add=True)
    
    class Meta:
        verbose_name = " - Заявка на дилерство"
        verbose_name_plural = "Заявки - Заявки на дилерство"
        ordering = ['-created_at']
    
    def __str__(self):
        company = f" ({self.company_name})" if self.company_name else ""
        return f"{self.name}{company} - {self.region}"

# ========== 05. ВАКАНСИИ ==========

class Vacancy(models.Model):
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
        status = "✅ Активна" if self.is_active else "❌ Неактивна"
        return f"{self.title} — {status}"
    
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

class JobApplication(models.Model):
    vacancy = models.ForeignKey(
        Vacancy, 
        on_delete=models.CASCADE, 
        related_name='applications', 
        verbose_name='Вакансия'
    )
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

# ========== amoCRM ТОКЕНЫ ==========

class AmoCRMToken(models.Model):
    access_token = models.TextField("Access Token")
    refresh_token = models.TextField("Refresh Token")
    expires_at = models.DateTimeField("Истекает")
    updated_at = models.DateTimeField("Последнее обновление", auto_now=True)
    
    class Meta:
        verbose_name = "amoCRM Токен"
        verbose_name_plural = "amoCRM Токены"
    
    def __str__(self):
        from django.utils import timezone
        if self.expires_at and self.expires_at > timezone.now():
            return f"✅ Токен валиден до {self.expires_at.strftime('%d.%m.%Y %H:%M')}"
        else:
            return f"❌ Токен истёк или не настроен"
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'access_token': '',
                'refresh_token': '',
                'expires_at': timezone.now() - timedelta(days=1)  
            }
        )
        return obj
    
    def is_expired(self):
        
        if not self.access_token or not self.refresh_token:
            return True
        
        return timezone.now() + timedelta(hours=1) >= self.expires_at

# ========== DASHBOARD (прокси-модель для админки) ==========

class Dashboard(models.Model):
    class Meta:
        managed = False  
        verbose_name = " Dashboard"
        verbose_name_plural = " Аналитика Dashboard"
        
        db_table = 'dashboard_proxy_table'
        
        default_permissions = ('view',)  

class Promotion(models.Model):
    title = models.CharField(max_length=200, verbose_name=_("Заголовок"))
    description = models.TextField(verbose_name=_("Описание"))
    image = models.ImageField(upload_to='promotions/', blank=True, null=True, verbose_name=_("Изображение"))
    link = models.URLField(blank=True, null=True, verbose_name=_("Ссылка"))
    button_text = models.CharField(max_length=50, default="Batafsil", verbose_name=_("Текст кнопки"))
    
    is_active = models.BooleanField(default=True, verbose_name=_("Активна"))
    show_on_homepage = models.BooleanField(default=True, verbose_name=_("Показывать на главной"))
    
    start_date = models.DateTimeField(default=timezone.now, verbose_name=_("Дата начала"))
    end_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Дата окончания"))
    
    priority = models.IntegerField(default=0, verbose_name=_("Приоритет"), 
                                   help_text=_("Чем выше число, тем выше в списке"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Создано"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Обновлено"))
    
    class Meta:
        verbose_name = _("Акция")
        verbose_name_plural = _("Акции")
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return self.title
    
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.end_date and self.end_date < now:
            return False
        if self.start_date > now:
            return False
        return True
    
# ========== SEO META DATA ==========

class PageMeta(models.Model):
    MODEL_CHOICES = [
        ('Page', 'Статическая страница'),
        ('Post', 'Новость'),
        ('Product', 'Продукт'),
    ]
    
    OG_TYPE_CHOICES = [
        ('website', 'Website - Обычный сайт'),
        ('article', 'Article - Статья, новость'),
        ('product', 'Product - Товар, продукт'),
        ('profile', 'Profile - Профиль'),
        ('video.movie', 'Video - Видео'),   
        ('music.song', 'Music - Музыка'),
        ('book', 'Book - Книга'),
    ]
    
    # ========== ИДЕНТИФИКАЦИЯ ==========
    model = models.CharField(
        "Тип страницы",
        max_length=50,
        choices=MODEL_CHOICES,
        help_text="Выберите категорию страницы"
    )
    
    key = models.CharField(
        "Ключ страницы",
        max_length=100,
        help_text="Уникальный идентификатор страницы"
    )
    
    # ========== ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ПРАВИЛЬНОЙ СОРТИРОВКИ ==========
    key_order = models.IntegerField(
        "Порядок сортировки",
        null=True,
        blank=True,
        db_index=True,
        editable=False,
        help_text="Автоматически заполняется из key для правильной сортировки"
    )
    
    # ========== БАЗОВЫЕ META ТЕГИ ==========
    title = models.CharField(
        "Title",
        max_length=255,
        help_text="Заголовок для поисковиков (оптимально: 50-70 символов)"
    )
    
    description = models.TextField(
        "Description",
        max_length=1000,
        help_text="Описание для поисковиков (оптимально: 150-250 символов)"
    )
    
    keywords = models.CharField(
        "Keywords",
        max_length=500,
        blank=True,
        null=True,
        help_text="Ключевые слова через запятую (необязательно)"
    )
    
    # ========== OPEN GRAPH (соцсети) ==========
    og_title = models.CharField(
        "OG Title",
        max_length=255,
        blank=True,
        null=True,
        help_text="Заголовок для соцсетей (если пусто - используется Title)"
    )
    
    og_description = models.TextField(
        "OG Description",
        max_length=1000,
        blank=True,
        null=True,
        help_text="Описание для соцсетей (если пусто - используется Description)"
    )
    
    og_url = models.URLField(
        "OG URL",
        blank=True,
        null=True,
        help_text="Полная ссылка на страницу (генерируется автоматически)"
    )
    
    og_type = models.CharField(
        "OG Type",
        max_length=50,
        choices=OG_TYPE_CHOICES,
        default='website',
        help_text="Тип контента для соцсетей"
    )
    
    og_site_name = models.CharField(
        "OG Site Name",
        max_length=100,
        default='FAW Uzbekistan',
        help_text="Название сайта/компании"
    )
    
    og_image = models.ImageField(
        "OG Image",
        upload_to="seo/og_images/",
        blank=True,
        null=True,
        help_text="Картинка для соцсетей (рекомендуется: 1200x630px)"
    )
    
    # ========== СЛУЖЕБНЫЕ ПОЛЯ ==========
    is_active = models.BooleanField(
        "Активно",
        default=True,
        help_text="Использовать эти мета-данные на сайте"
    )
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    
    class Meta:
        verbose_name = "SEO - Мета-данные страницы"
        verbose_name_plural = "SEO - Мета-данные страниц"
        ordering = ['-is_active', '-updated_at', 'model', 'key_order', 'key']
        unique_together = ('model', 'key')
    
    def __str__(self):
        return f"{self.get_model_display()} — {self.key}"
    
    def save(self, *args, **kwargs):
        if self.key.isdigit():
            self.key_order = int(self.key)
        else:
            self.key_order = 999999
        
        super().save(*args, **kwargs)
    
    def get_og_title(self):
        return self.og_title or self.title
    
    def get_og_description(self):
        return self.og_description or self.description
    
    def get_full_url(self):
        if self.og_url:
            return self.og_url
        
        base_url = 'https://faw.uz'
        
        # ========== ДЛЯ СТАТИЧЕСКИХ СТРАНИЦ ==========
        if self.model == 'Page':
            url_map = {
                'home': '/',
                'about': '/about/',
                'contact': '/contact/',
                'products': '/products/',
                'dealers': '/dealers/',
                'jobs': '/jobs/',
                'lizing': '/lizing/',
                'become-a-dealer': '/become-a-dealer/',
                'news': '/news/',
                'services': '/services/',
            }
            path = url_map.get(self.key, '/')
            return f"{base_url}{path}"
        
        # ========== ДЛЯ НОВОСТЕЙ ==========
        elif self.model == 'Post':
            if self.key.isdigit():
                try:
                    from main.models import News
                    news = News.objects.get(id=int(self.key))
                    return f"{base_url}/news/{news.slug}/"
                except (News.DoesNotExist, ValueError):
                    return f"{base_url}/news/"
            return f"{base_url}/news/"
        
        # ========== ДЛЯ ПРОДУКТОВ ==========
        elif self.model == 'Product':
            if self.key.isdigit():
                try:
                    from main.models import Product
                    product = Product.objects.get(id=int(self.key))
                    return f"{base_url}/products/{product.slug}/"
                except (Product.DoesNotExist, ValueError):
                    return f"{base_url}/products/"
            return f"{base_url}/products/"


# ========== FAQ ==========

class FAQItem(models.Model):
    question = models.CharField("Вопрос", max_length=500)
    answer = models.TextField("Ответ")
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "FAQ — вопрос"
        verbose_name_plural = "FAQ — вопросы"
        ordering = ['order']

    def __str__(self):
        return self.question or f"FAQ #{self.pk}"
    

# ========== КОНТАКТЫ БОТА ==========

class BotContacts(models.Model):

    phone_main = models.CharField(
        "Основной телефон",
        max_length=50,
        default="+998 71 000-00-00",
        help_text="Например: +998 71 234-56-78",
    )
    phone_secondary = models.CharField(
        "Дополнительный телефон",
        max_length=50,
        blank=True,
        null=True,
    )
    email = models.EmailField(
        "Email",
        default="info@faw.uz",
    )
    address_ru = models.TextField(
        "Адрес (RU)",
        default="г. Ташкент, ул. Абдулла Каххара 2А",
    )
    address_uz = models.TextField(
        "Адрес (UZ)",
        default="Toshkent sh., Abdulla Kaxxar ko'chasi 2A",
    )
    address_en = models.TextField(
        "Адрес (EN)",
        blank=True,
        null=True,
    )
    working_hours_ru = models.CharField(
        "Рабочее время (RU)",
        max_length=200,
        default="Пн–Пт: 09:00–18:00, Сб: 09:00–14:00",
    )
    working_hours_uz = models.CharField(
        "Рабочее время (UZ)",
        max_length=200,
        default="Du–Ju: 09:00–18:00, Sha: 09:00–14:00",
    )
    working_hours_en = models.CharField(
        "Рабочее время (EN)",
        max_length=200,
        blank=True,
        null=True,
    )

    # Соцсети
    telegram_channel = models.CharField(
        "Telegram канал",
        max_length=100,
        blank=True,
        null=True,
        help_text="Например: https://t.me/faw_uzbekistan",
    )
    instagram = models.CharField(
        "Instagram",
        max_length=100,
        blank=True,
        null=True,
        help_text="Например: https://instagram.com/faw.uz",
    )
    youtube = models.CharField(
        "YouTube",
        max_length=200,
        blank=True,
        null=True,
        help_text="Ссылка на канал",
    )
    facebook = models.CharField(
        "Facebook",
        max_length=200,
        blank=True,
        null=True,
    )
    linkedin = models.CharField(
        "LinkedIn",
        max_length=200,
        blank=True,
        null=True,
    )
    website = models.URLField(
        "Сайт",
        default="https://faw.uz",
    )

    map_url = models.URLField(
        "Ссылка на карту (2GIS/Google)",
        blank=True,
        null=True,
        help_text="Ссылка на офис в 2GIS или Google Maps",
    )

    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Бот — Контакты"
        verbose_name_plural = "Бот — Контакты"

    def __str__(self):
        return f"Контакты FAW.UZ (обновлено {self.updated_at.strftime('%d.%m.%Y')})"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'phone_main': '+998 71 000-00-00',
                'email': 'info@faw.uz',
            },
        )
        return obj

class TelegramUser(models.Model):

    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('uz', "O'zbekcha"),
        ('en', 'English'),
    ]

    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('interested', 'Интересующийся'),
        ('hot', 'Горячий'),
        ('client', 'Клиент'),
        ('vip', 'VIP'),
    ]

    telegram_id = models.BigIntegerField(
        "Telegram ID",
        unique=True,
        db_index=True,
    )
    username = models.CharField(
        "Username",
        max_length=100,
        blank=True,
        null=True,
    )
    first_name = models.CharField(
        "Имя",
        max_length=100,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=100,
        blank=True,
        null=True,
    )
    middle_name = models.CharField(
        "Отчество",
        max_length=100,
        blank=True,
        null=True,
    )
    phone = models.CharField(
        "Телефон",
        max_length=20,
        blank=True,
        null=True,
    )
    age = models.PositiveSmallIntegerField(
        "Возраст",
        blank=True,
        null=True,
    )
    region = models.CharField(
        "Регион",
        max_length=100,
        choices=REGION_CHOICES,
        blank=True,
        null=True,
    )
    language = models.CharField(
        "Язык",
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='ru',
    )
    status = models.CharField(
        "Статус клиента",
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
    )
    is_blocked = models.BooleanField(
        "Заблокировал бота",
        default=False,
        help_text="Пользователь нажал Stop или заблокировал бота",
    )
    notifications_enabled = models.BooleanField(
        "Уведомления включены",
        default=True,
    )
    # Источник — откуда пришёл в бот
    referral_code = models.CharField(
        "Реферальный код",
        max_length=50,
        blank=True,
        null=True,
        help_text="Код из ссылки ?start=ref_XXXXX",
    )
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        verbose_name="Пригласил",
    )
    # Статистика
    total_requests = models.PositiveIntegerField(
        "Всего заявок",
        default=0,
    )
    last_active = models.DateTimeField(
        "Последняя активность",
        auto_now=True,
    )
    created_at = models.DateTimeField(
        "Дата регистрации",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Бот — Пользователь"
        verbose_name_plural = "Бот — Пользователи"
        ordering = ['-created_at']

    def __str__(self):
        name = self.first_name or self.username or str(self.telegram_id)
        return f"{name} ({self.get_language_display()})"

    @property
    def full_name(self) -> str:
        parts = filter(None, [self.last_name, self.first_name, self.middle_name])
        return " ".join(parts) or "—"

    def get_referral_link(self, bot_username: str) -> str:
        return f"https://t.me/{bot_username}?start=ref_{self.telegram_id}"


class TestDriveRequest(models.Model):

    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('confirmed', 'Подтверждена'),
        ('visited', 'Клиент пришёл'),
        ('no_show', 'Не явился'),
        ('cancelled', 'Отменена'),
    ]

    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='test_drives',
        verbose_name="Пользователь",
    )
    dealer = models.ForeignKey(
        Dealer,
        on_delete=models.SET_NULL,
        null=True,
        related_name='test_drive_requests',
        verbose_name="Дилер",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='test_drive_requests',
        verbose_name="Модель",
    )

    client_name = models.CharField("Имя клиента", max_length=200)
    client_phone = models.CharField("Телефон клиента", max_length=20)

    preferred_date = models.DateField("Желаемая дата")
    preferred_time = models.CharField(
        "Желаемое время",
        max_length=10,
        help_text="Например: 10:00",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True,
    )
    reminder_sent = models.BooleanField(
        "Напоминание отправлено",
        default=False,
    )
    feedback_requested = models.BooleanField(
        "Запрос отзыва отправлен",
        default=False,
    )
    admin_comment = models.TextField(
        "Комментарий менеджера",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField("Дата заявки", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Бот — Заявка тест-драйв"
        verbose_name_plural = "Бот — Заявки тест-драйв"
        ordering = ['-created_at']

    def __str__(self):
        date_str = self.preferred_date.strftime('%d.%m.%Y') if self.preferred_date else '—'
        product_name = self.product.title if self.product else '—'
        return f"{self.client_name} — {product_name} — {date_str}"


class BotConfig(models.Model):
    bot_token = models.CharField(
        "Токен бота",
        max_length=200,
        help_text="Получить у @BotFather. При смене — бот автоматически переключится на новый.",
    )
    bot_username = models.CharField(
        "Username бота",
        max_length=100,
        help_text="Например: faw_uz_bot (без @)",
        blank=True,
        null=True,
    )
    notify_chat_id = models.CharField(
        "Chat ID для уведомлений",
        max_length=50,
        help_text="ID группы/канала куда летят уведомления о заявках из бота",
    )
    notify_chat_id_2 = models.CharField(
        "Chat ID для уведомлений (резерв)",
        max_length=50,
        blank=True,
        null=True,
        help_text="Дополнительный чат, например личка старшего менеджера",
    )
    site_url = models.URLField(
        "URL сайта",
        default="https://faw.uz",
        help_text="Используется в кнопках 'Подробнее на сайте'",
    )
    is_active = models.BooleanField(
        "Бот активен",
        default=True,
        help_text="Если выключить — бот перестанет отвечать на сообщения",
    )
    use_webhook = models.BooleanField(
        "Использовать Webhook",
        default=False,
        help_text="True = Webhook (прод), False = Polling (локально)",
    )
    webhook_url = models.URLField(
        "Webhook URL",
        blank=True,
        null=True,
        help_text="Например: https://faw.uz/bot/webhook/",
    )
    work_hours_start = models.TimeField(
        "Начало рабочего дня",
        default=datetime_time(9, 0),
        help_text="Время по Ташкенту (UTC+5)",
    )
    work_hours_end = models.TimeField(
        "Конец рабочего дня",
        default=datetime_time(18, 0),
        help_text="Время по Ташкенту (UTC+5)",
    )

    catalog_file = models.FileField(
        "PDF каталог",
        upload_to="bot/catalog/",
        blank=True,
        null=True,
        help_text="PDF файл каталога. Отправляется пользователю по кнопке 'Скачать каталог'",
    )

    updated_at = models.DateTimeField("Последнее обновление", auto_now=True)

    class Meta:
        verbose_name = "Бот — Конфигурация"
        verbose_name_plural = "Бот — Конфигурация"

    def __str__(self):
        status = "✅ Активен" if self.is_active else "❌ Выключен"
        return f"Конфигурация бота — {status}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'bot_token': '',
                'notify_chat_id': '',
                'is_active': False,
            },
        )
        return obj


class BotMessage(models.Model):

    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('uz', "O'zbekcha"),
        ('en', 'English'),
    ]

    key = models.CharField(
        "Ключ",
        max_length=100,
        db_index=True,
        help_text="Уникальный идентификатор текста. Например: welcome, main_menu, td_success",
    )
    language = models.CharField(
        "Язык",
        max_length=5,
        choices=LANGUAGE_CHOICES,
    )
    text = models.TextField(
        "Текст",
        help_text="Поддерживает HTML теги: <b>, <i>, <code>. Переменные: {name}, {phone}",
    )
    description = models.CharField(
        "Описание (для менеджера)",
        max_length=200,
        blank=True,
        help_text="Где используется этот текст",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Бот — Текст"
        verbose_name_plural = "Бот — Тексты"
        unique_together = ('key', 'language')
        ordering = ['key', 'language']

    def __str__(self):
        return f"{self.key} [{self.language}]"


class BotMenuItem(models.Model):
    KEY_CHOICES = [
        ('catalog', '🚗 Каталог'),
        ('dealers', '🏢 Дилеры'),
        ('news', '📰 Новости'),
        ('promotions', '🎯 Акции'),
        ('test_drive', '📋 Тест-драйв'),
        ('lead', '📞 Оставить заявку'),
        ('leasing', '💰 Лизинг'),
        ('faq', '❓ FAQ'),
        ('contacts', '📍 Контакты'),
        ('profile', '👤 Профиль'),
        ('language', '🌐 Язык'),
    ]

    key = models.CharField(
        "Ключ",
        max_length=50,
        choices=KEY_CHOICES,
        unique=True,
    )
    label_ru = models.CharField("Название (RU)", max_length=50)
    label_uz = models.CharField("Название (UZ)", max_length=50)
    label_en = models.CharField("Название (EN)", max_length=50)
    emoji = models.CharField(
        "Эмодзи",
        max_length=5,
        default="📌",
    )
    order = models.PositiveSmallIntegerField(
        "Порядок",
        default=0,
        help_text="Чем меньше число — тем выше кнопка",
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
        help_text="Скрыть пункт меню без удаления",
    )

    class Meta:
        verbose_name = "Бот — Пункт меню"
        verbose_name_plural = "Бот — Меню"
        ordering = ['order']

    def __str__(self):
        status = "✅" if self.is_active else "❌"
        return f"{status} {self.order}. {self.emoji} {self.label_ru}"

    def get_label(self, language: str) -> str:
        labels = {'ru': self.label_ru, 'uz': self.label_uz, 'en': self.label_en}
        label = labels.get(language, self.label_ru)
        if self.emoji:
            return f"{self.emoji} {label}"
        return label


class BotBroadcast(models.Model):
    TARGET_CHOICES = [
        ('all', 'Все пользователи'),
        ('ru', 'Только русскоязычные'),
        ('uz', "Только узбекоязычные"),
        ('en', 'Только англоязычные'),
        ('hot', 'Горячие клиенты'),
        ('vip', 'VIP клиенты'),
        ('active_30', 'Активные за 30 дней'),
        ('region', 'По региону'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('scheduled', 'Запланирована'),
        ('sending', 'Отправляется'),
        ('done', 'Отправлена'),
        ('failed', 'Ошибка'),
    ]

    title = models.CharField(
        "Название",
        max_length=200,
        help_text="Внутреннее название для менеджера",
    )
    text_ru = models.TextField("Текст (RU)", blank=True)
    text_uz = models.TextField("Текст (UZ)", blank=True)
    text_en = models.TextField("Текст (EN)", blank=True)
    image = models.ImageField(
        "Изображение",
        upload_to="bot/broadcasts/",
        blank=True,
        null=True,
        help_text="Опционально — прикрепить фото к рассылке",
    )
    button_text = models.CharField(
        "Текст кнопки",
        max_length=100,
        blank=True,
        null=True,
        help_text="Например: Узнать подробнее",
    )
    button_url = models.URLField(
        "Ссылка кнопки",
        blank=True,
        null=True,
    )
    target = models.CharField(
        "Аудитория",
        max_length=20,
        choices=TARGET_CHOICES,
        default='all',
    )
    target_region = models.CharField(
        "Регион (если выбран по региону)",
        max_length=100,
        choices=REGION_CHOICES,
        blank=True,
        null=True,
    )
    scheduled_at = models.DateTimeField(
        "Запланировано на",
        blank=True,
        null=True,
        help_text="Оставить пустым = отправить сразу после статуса 'Запланирована'",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
    )
    total_recipients = models.PositiveIntegerField("Получателей", default=0)
    sent_count = models.PositiveIntegerField("Отправлено", default=0)
    failed_count = models.PositiveIntegerField("Ошибок", default=0)
    blocked_count = models.PositiveIntegerField("Заблокировали бота", default=0)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Создал",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField("Отправлено в", blank=True, null=True)

    class Meta:
        verbose_name = "Бот — Рассылка"
        verbose_name_plural = "Бот — Рассылки"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"

    def get_text(self, language: str) -> str:
        texts = {'ru': self.text_ru, 'uz': self.text_uz, 'en': self.text_en}
        return texts.get(language) or self.text_ru


class ProductWishlist(models.Model):
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='wishlist',
        verbose_name="Пользователь",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
        verbose_name="Продукт",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Бот — Избранное"
        verbose_name_plural = "Бот — Избранное"
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} → {self.product.title}"


class ProductViewHistory(models.Model):
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='view_history',
        verbose_name="Пользователь",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name="Продукт",
    )
    view_count = models.PositiveIntegerField("Количество просмотров", default=1)
    last_viewed = models.DateTimeField("Последний просмотр", auto_now=True)

    class Meta:
        verbose_name = "Бот — История просмотров"
        verbose_name_plural = "Бот — История просмотров"
        unique_together = ('user', 'product')
        ordering = ['-last_viewed']

    def __str__(self):
        return f"{self.user} → {self.product.title} ({self.view_count}x)"
    
# ═══════════════════════════════════════════════════════════════════
# СИГНАЛЫ — автоматический сброс кеша бота при изменении в Admin
# ═══════════════════════════════════════════════════════════════════

@receiver(post_save, sender=BotContacts)
def clear_bot_contacts_cache(sender, instance, **kwargs):
    cache.delete('bot_contacts')


@receiver(post_save, sender=BotConfig)
def clear_bot_config_cache(sender, instance, **kwargs):
    cache.delete('bot_config')


@receiver(post_save, sender=BotMessage)
def clear_bot_message_cache(sender, instance, **kwargs):
    cache.delete(f'bot_msg_{instance.key}_{instance.language}')


class BotFSMState(models.Model):
    key = models.CharField(max_length=255, unique=True, db_index=True)
    state = models.TextField(blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Бот — FSM состояние'
        verbose_name_plural = 'Бот — FSM состояния'

    def __str__(self):
        return f'{self.key}: {self.state}'