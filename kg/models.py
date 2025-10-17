from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils.text import slugify
from unidecode import unidecode
import uuid

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
        verbose_name = 'Машина'
        verbose_name_plural = '[KG] Каталог машин'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        print(f"\n=== СОХРАНЕНИЕ KGVehicle ===")
        print(f"ID: {self.pk}")
        print(f"title_ru: {self.title_ru}")
        
        # 1. ГЕНЕРАЦИЯ SLUG
        if self.title_ru:
            if not self.slug_ru:
                base_slug = slugify(unidecode(self.title_ru))
                counter = 1
                unique_slug = base_slug
                while KGVehicle.objects.filter(slug_ru=unique_slug).exclude(pk=self.pk).exists():
                    unique_slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug_ru = unique_slug
                print(f"✓ Создан slug_ru: {self.slug_ru}")
            
            self.slug = self.slug_ru or f"vehicle-{uuid.uuid4().hex[:12]}"
        
        if not self.slug or self.slug == '':
            self.slug = f"vehicle-{uuid.uuid4().hex[:12]}"
            print(f"✓ Создан дефолтный slug: {self.slug}")
        
        # Slug для KY и EN
        if self.title_ky and not self.slug_ky:
            self.slug_ky = slugify(unidecode(self.title_ky))
            print(f"✓ Создан slug_ky: {self.slug_ky}")
        
        if self.title_en and not self.slug_en:
            self.slug_en = slugify(self.title_en)
            print(f"✓ Создан slug_en: {self.slug_en}")
        
        # 2. ОПРЕДЕЛЕНИЕ КАТЕГОРИИ
        title_lower = (self.title_ru or self.title or '').lower()
        print(f"Анализ названия для категории: '{title_lower}'")
        
        if 'vr' in title_lower:
            self.category = 'vr'
            print(f"✓ Категория: VR Series")
        elif 'vh' in title_lower:
            self.category = 'vh'
            print(f"✓ Категория: VH Series")
        else:
            self.category = 'v'
            print(f"✓ Категория: V Series")
        
        print(f"Финальная категория: {self.category}")
        print("=== КОНЕЦ СОХРАНЕНИЯ ===\n")
        
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
        verbose_name = ' Доп. изображение'
        verbose_name_plural = 'Доп. изображения'
        ordering = ['order']


class VehicleCardSpec(models.Model):
    """Характеристики для карточки"""
    vehicle = models.ForeignKey(KGVehicle, related_name='card_specs', on_delete=models.CASCADE)
    icon = models.ImageField(upload_to='kg_vehicles/card_icons/', verbose_name='Иконка', blank=True, null=True)
    value_ru = models.CharField(max_length=100, verbose_name='Значение (RU)')
    value_ky = models.CharField(max_length=100, blank=True, verbose_name='Значение (KY)')
    value_en = models.CharField(max_length=100, blank=True, verbose_name='Значение (EN)')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['order']
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'

    def get_value(self, lang='ru'):
        if lang == 'en':
            return self.value_en or self.value_ru
        elif lang == 'ky':
            return self.value_ky or self.value_ru
        return self.value_ru
    
    def save(self, *args, **kwargs):
        print(f"\n=== СОХРАНЕНИЕ VehicleCardSpec ===")
        print(f"value_ru: {self.value_ru}")
        print(f"value_ky (до): {self.value_ky}")
        print(f"value_en (до): {self.value_en}")
        
        if self.value_ru:
            if not self.value_ky or self.value_ky.strip() == '':
                self.value_ky = self.auto_translate(self.value_ru, 'ky')
                print(f"✓ Автоперевод KY: {self.value_ky}")
            else:
                print(f"⊘ KY уже заполнено")
            
            if not self.value_en or self.value_en.strip() == '':
                self.value_en = self.auto_translate(self.value_ru, 'en')
                print(f"✓ Автоперевод EN: {self.value_en}")
            else:
                print(f"⊘ EN уже заполнено")
        
        print(f"value_ky (после): {self.value_ky}")
        print(f"value_en (после): {self.value_en}")
        print("=== КОНЕЦ СОХРАНЕНИЯ ===\n")
        
        super().save(*args, **kwargs)
    
    def auto_translate(self, text, lang):
       
        translations = {
            'Дизель': {'ky': 'Дизель', 'en': 'Diesel'},
            'Бензин': {'ky': 'Бензин', 'en': 'Gasoline'},
            'кг': {'ky': 'кг', 'en': 'kg'},
            'л.с.': {'ky': 'а.к.', 'en': 'hp'},
            'м²': {'ky': 'м²', 'en': 'm²'},
            'м³': {'ky': 'м³', 'en': 'm³'},
            'л': {'ky': 'л', 'en': 'L'},
            'Климат-контроль': {'ky': 'Климат-контроль', 'en': 'Climate control'},  # ← КРИТИЧНО!
            'Кондиционер': {'ky': 'Кондиционер', 'en': 'Air conditioning'},
            '4x2': {'ky': '4x2', 'en': '4x2'},
            '4×2': {'ky': '4×2', 'en': '4×2'},
            '4х2': {'ky': '4х2', 'en': '4х2'},
            '4 х 2': {'ky': '4 х 2', 'en': '4 х 2'},
            'Передний': {'ky': 'Алдыңкы', 'en': 'Front'},
            'Задний': {'ky': 'Арткы', 'en': 'Rear'},
            'Полный': {'ky': 'Толук', 'en': 'Full'},
            'Механика': {'ky': 'Механикалык', 'en': 'Manual'},
            'Автомат': {'ky': 'Автоматтык', 'en': 'Automatic'},
            'Робот': {'ky': 'Робот', 'en': 'Robot'},
        }
        
        if text in translations:
            return translations[text].get(lang, text)
        
        result = text
        for ru_term, trans in translations.items():
            if ru_term in text:
                result = result.replace(ru_term, trans.get(lang, ru_term))
        
        return result


class IconTemplate(models.Model):
    """Шаблонные иконки для выбора"""
    name = models.CharField(max_length=50, verbose_name='Название', unique=True)
    icon = models.ImageField(upload_to='kg_vehicles/card_icons/', verbose_name='Иконка')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Шаблон иконки'
        verbose_name_plural = 'Шаблоны иконок'
    
    def __str__(self):
        return self.name


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
        verbose_name = 'Заявка'
        verbose_name_plural = '[KG] Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d.%m.%Y')}"


class KGHeroSlide(models.Model):
    """Hero-слайды для главной страницы"""
    vehicle = models.ForeignKey(KGVehicle, on_delete=models.CASCADE, verbose_name='Машина')
    
    description_ru = models.TextField(max_length=500, verbose_name='Описание (RU)', default='')
    description_ky = models.TextField(max_length=500, verbose_name='Описание (KY)', blank=True, default='')
    description_en = models.TextField(max_length=500, verbose_name='Описание (EN)', blank=True, default='')
    
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        ordering = ['order']
        verbose_name = ' Hero-слайд'
        verbose_name_plural = '[KG] Hero-слайды'

    def __str__(self):
        return f"Hero #{self.order} - {self.vehicle.title}"
    
    def get_description(self, lang='ru'):
        if lang == 'en':
            return self.description_en or self.description_ru
        elif lang == 'ky':
            return self.description_ky or self.description_ru
        return self.description_ru