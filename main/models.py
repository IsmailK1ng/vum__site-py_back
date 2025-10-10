# main/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# ============ Модели для faw.uz ============
class News(models.Model):
    """Основная модель новости"""
    title = models.CharField("Заголовок", max_length=255)
    desc = models.TextField("Краткое описание", max_length=500, help_text="Краткое описание для карточки новости")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    author_photo = models.ImageField("Фото автора", upload_to="authors/", blank=True, null=True)
    preview_image = models.ImageField("Главное фото", upload_to="news/previews/", blank=True, null=True)
    created_at = models.DateTimeField("Дата публикации", auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"


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
        verbose_name = "Блок новости"
        verbose_name_plural = "Блоки новостей"

    def __str__(self):
        return f"{self.news.title} — {self.block_type}"


class ContactForm(models.Model):
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
    
    name = models.CharField(max_length=255, verbose_name='Имя')
    region = models.CharField(max_length=100, choices=REGION_CHOICES, verbose_name='Регион')
    phone = models.CharField(max_length=50, verbose_name='Телефон')
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время отправки')
    is_processed = models.BooleanField(default=False, verbose_name='Просмотрено')
    admin_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий администратора')

    class Meta:
        verbose_name = 'Заявка (UZ)'
        verbose_name_plural = 'Заявки (UZ)'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.phone} ({self.created_at.strftime('%d.%m.%Y')})"


# ============ Модели для faw.kg ============


# main/models.py (только KG часть, UZ модели не трогаем)

# ============ Модели для faw.kg ============
class KGVehicle(models.Model):
    """Модель машины для Киргизстана"""
    # Основные поля (для всех языков по умолчанию - русский)
    title = models.CharField(max_length=255, verbose_name='Название', default='')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='URL-имя')
    
    # Переводы названия (вручную)
    title_ru = models.CharField(max_length=255, verbose_name='Название (RU)', blank=True, null=True)
    title_ky = models.CharField(max_length=255, verbose_name='Название (KY)', blank=True, null=True)
    title_en = models.CharField(max_length=255, verbose_name='Название (EN)', blank=True, null=True)
    
    # Переводы URL (вручную)
    slug_ru = models.SlugField(max_length=255, verbose_name='URL (RU)', blank=True, null=True)
    slug_ky = models.SlugField(max_length=255, verbose_name='URL (KY)', blank=True, null=True)
    slug_en = models.SlugField(max_length=255, verbose_name='URL (EN)', blank=True, null=True)
    
    # Изображения (одинаковые для всех языков)
    preview_image = models.ImageField(
        upload_to='kg_vehicles/previews/', 
        blank=True, 
        null=True, 
        verbose_name='Превью для каталога'
    )
    main_image = models.ImageField(
        upload_to='kg_vehicles/main/', 
        blank=True, 
        null=True, 
        verbose_name='Главное изображение'
    )
    
    # Характеристики с переводами (JSON)
    specs = models.JSONField(blank=True, null=True, verbose_name='Характеристики (по умолчанию)', default=dict)
    specs_ru = models.JSONField(blank=True, null=True, verbose_name='Характеристики (RU)', default=dict)
    specs_ky = models.JSONField(blank=True, null=True, verbose_name='Характеристики (KY)', default=dict)
    specs_en = models.JSONField(blank=True, null=True, verbose_name='Характеристики (EN)', default=dict)
    
    # Служебные поля
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Машина (KG)'
        verbose_name_plural = 'Машины (KG)'
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.title_ru or self.slug


class FeatureIcon(models.Model):
    """Иконки особенностей машин"""
    name = models.CharField(max_length=100, verbose_name='Название иконки')
    image = models.ImageField(upload_to='kg_vehicles/features/', verbose_name='Изображение иконки')

    class Meta:
        verbose_name = 'Иконка особенности'
        verbose_name_plural = 'Иконки особенностей'

    def __str__(self):
        return self.name


class KGVehicleFeature(models.Model):
    """Связь машины с её особенностями"""
    vehicle = models.ForeignKey(KGVehicle, related_name='vehicle_features', on_delete=models.CASCADE, verbose_name='Машина')
    feature = models.ForeignKey(FeatureIcon, on_delete=models.CASCADE, verbose_name='Особенность')

    class Meta:
        verbose_name = 'Особенность машины (KG)'
        verbose_name_plural = 'Особенности машин (KG)'
        unique_together = ('vehicle', 'feature')

    def __str__(self):
        return f"{self.vehicle.title} - {self.feature.name}"


class KGVehicleImage(models.Model):
    """Дополнительные изображения машины"""
    vehicle = models.ForeignKey(KGVehicle, related_name='mini_images', on_delete=models.CASCADE, verbose_name='Машина')
    image = models.ImageField(upload_to='kg_vehicles/mini/%Y/%m/', verbose_name='Изображение')
    alt = models.CharField(max_length=255, blank=True, verbose_name='Alt текст')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Дополнительное изображение (KG)'
        verbose_name_plural = 'Дополнительные изображения (KG)'
        ordering = ['order']

    def __str__(self):
        return f"Изображение для {self.vehicle.title}"


class KGFeedback(models.Model):
    """Заявки с сайта faw.kg"""
    REGION_CHOICES = [
        ('Bishkek', 'Бишкек'),
        ('Osh', 'Ош'),
        ('Chuy', 'Чуйская область'),
        ('Jalal-Abad', 'Джалал-Абадская область'),
        ('Naryn', 'Нарынская область'),
        ('Batken', 'Баткенская область'),
        ('Talas', 'Таласская область'),
        ('Issyk-Kul', 'Иссык-Кульская область'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='ФИО')
    phone = models.CharField(max_length=50, verbose_name='Телефон', validators=[
        RegexValidator(
            regex=r'^\+996\d{9}$',
            message='Телефон должен быть в формате +996XXXXXXXXX',
        ),
    ])
    region = models.CharField(max_length=100, choices=REGION_CHOICES, verbose_name='Регион')
    vehicle = models.ForeignKey(
        KGVehicle, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        verbose_name='Машина', 
        related_name='feedbacks'
    )
    message = models.TextField(verbose_name='Сообщение', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время отправки')
    is_processed = models.BooleanField(default=False, verbose_name='Обработано')
    admin_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий администратора')

    class Meta:
        verbose_name = 'Заявка (KG)'
        verbose_name_plural = 'Заявки (KG)'
        ordering = ['-created_at']

    def __str__(self):
        vehicle_name = self.vehicle.title if self.vehicle else 'Без машины'
        return f"{self.name} - {vehicle_name} ({self.created_at.strftime('%d.%m.%Y')})"
    """Заявки с сайта faw.kg"""
    REGION_CHOICES = [
        ('Bishkek', 'Бишкек'),
        ('Osh', 'Ош'),
        ('Chuy', 'Чуйская область'),
        ('Jalal-Abad', 'Джалал-Абадская область'),
        ('Naryn', 'Нарынская область'),
        ('Batken', 'Баткенская область'),
        ('Talas', 'Таласская область'),
        ('Issyk-Kul', 'Иссык-Кульская область'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='ФИО')
    phone = models.CharField(max_length=50, verbose_name='Телефон', validators=[
        RegexValidator(
            regex=r'^\+996\d{9}$',
            message='Телефон должен быть в формате +996XXXXXXXXX',
        ),
    ])
    region = models.CharField(max_length=100, choices=REGION_CHOICES, verbose_name='Регион')
    vehicle = models.ForeignKey(KGVehicle, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Машина', related_name='feedbacks')
    message = models.TextField(verbose_name='Сообщение', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время отправки')
    is_processed = models.BooleanField(default=False, verbose_name='Обработано')
    admin_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий администратора')

    class Meta:
        verbose_name = 'Заявка (KG)'
        verbose_name_plural = 'Заявки (KG)'
        ordering = ['-created_at']

    def __str__(self):
        vehicle_name = self.vehicle.title if self.vehicle else 'Без машины'
        return f"{self.name} - {vehicle_name} ({self.created_at.strftime('%d.%m.%Y')})"