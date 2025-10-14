from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# ============ ТОЛЬКО FAW.KG ============

class KGVehicle(models.Model):
    """Модель машины для Киргизстана"""
    
    title = models.CharField(max_length=255, verbose_name='Название', default='')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='URL-имя')
    
    CATEGORY_CHOICES = [
        ('v', 'V Series'),
        ('vr', 'VR Series'),
        ('vh', 'VH Series'),
    ]
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='v', verbose_name='Серия')
    
    # Переводы
    title_ru = models.CharField(max_length=255, verbose_name='Название (RU)', blank=True, null=True)
    title_ky = models.CharField(max_length=255, verbose_name='Название (KY)', blank=True, null=True)
    title_en = models.CharField(max_length=255, verbose_name='Название (EN)', blank=True, null=True)
    
    slug_ru = models.SlugField(max_length=255, verbose_name='URL (RU)', blank=True, null=True)
    slug_ky = models.SlugField(max_length=255, verbose_name='URL (KY)', blank=True, null=True)
    slug_en = models.SlugField(max_length=255, verbose_name='URL (EN)', blank=True, null=True)
    
    # Изображения
    preview_image = models.ImageField(upload_to='kg_vehicles/previews/', blank=True, null=True, verbose_name='Превью')
    main_image = models.ImageField(upload_to='kg_vehicles/main/', blank=True, null=True, verbose_name='Главное фото')
    
    # Характеристики
    specs_ru = models.JSONField(blank=True, null=True, default=dict, verbose_name='Характеристики (RU)')
    specs_ky = models.JSONField(blank=True, null=True, default=dict, verbose_name='Характеристики (KY)')
    specs_en = models.JSONField(blank=True, null=True, default=dict, verbose_name='Характеристики (EN)')
    
    # Служебные
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = '[KG] Машина'
        verbose_name_plural = '[KG] Каталог машин'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        title_lower = (self.title or self.title_ru or '').lower()
        if 'vr' in title_lower:
            self.category = 'vr'
        elif 'vh' in title_lower:
            self.category = 'vh'
        else:
            self.category = 'v'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title_ru or self.title or self.slug
    
    def get_title(self, lang='ru'):
        if lang == 'en':
            return self.title_en or self.title_ru or self.title
        elif lang == 'ky':
            return self.title_ky or self.title_ru or self.title
        return self.title_ru or self.title
    
    def get_slug(self, lang='ru'):
        if lang == 'en':
            return self.slug_en or self.slug_ru or self.slug
        elif lang == 'ky':
            return self.slug_ky or self.slug_ru or self.slug
        return self.slug_ru or self.slug
    
    def get_specs(self, lang='ru'):
        if lang == 'en':
            return self.specs_en or self.specs_ru or {}
        elif lang == 'ky':
            return self.specs_ky or self.specs_ru or {}
        return self.specs_ru or {}


class KGVehicleImage(models.Model):
    """Дополнительные изображения"""
    vehicle = models.ForeignKey(KGVehicle, related_name='mini_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='kg_vehicles/mini/%Y/%m/')
    alt = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = '[KG] Доп. изображение'
        verbose_name_plural = '[KG] Доп. изображения'
        ordering = ['order']


class VehicleCardSpec(models.Model):
    """Характеристики для карточки"""
    vehicle = models.ForeignKey(KGVehicle, related_name='card_specs', on_delete=models.CASCADE)
    icon = models.ImageField(upload_to='kg_vehicles/card_icons/')
    value_ru = models.CharField(max_length=100)
    value_ky = models.CharField(max_length=100, blank=True)
    value_en = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = '[KG] Характеристика'
        verbose_name_plural = '[KG] Характеристики'

    def get_value(self, lang='ru'):
        if lang == 'en':
            return self.value_en or self.value_ru
        elif lang == 'ky':
            return self.value_ky or self.value_ru
        return self.value_ru


class KGFeedback(models.Model):
    """Заявки с faw.kg"""
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
    
    name = models.CharField(max_length=255, verbose_name='ФИО')
    phone = models.CharField(max_length=50, verbose_name='Телефон')
    region = models.CharField(max_length=100, choices=REGION_CHOICES, verbose_name='Регион')
    vehicle = models.ForeignKey(KGVehicle, null=True, blank=True, on_delete=models.SET_NULL, related_name='feedbacks')
    message = models.TextField(blank=True, null=True, verbose_name='Сообщение')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='Приоритет')
    manager = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='kg_feedbacks')
    
    created_at = models.DateTimeField(auto_now_add=True)
    admin_comment = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = '[KG] Заявка'
        verbose_name_plural = '[KG] Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d.%m.%Y')}"


class KGHeroSlide(models.Model):
    """Hero-слайды"""
    vehicle = models.ForeignKey(KGVehicle, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = '[KG] Hero-слайд'
        verbose_name_plural = '[KG] Hero-слайды'

    def __str__(self):
        return f"Hero #{self.order} - {self.vehicle.title}"