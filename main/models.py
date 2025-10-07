from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


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
    
    name = models.CharField(max_length=255, verbose_name='Ism')
    region = models.CharField(max_length=100, choices=REGION_CHOICES, verbose_name='Viloyat')
    phone = models.CharField(max_length=50, verbose_name='Telefon')
    message = models.TextField(verbose_name='Xabar')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yuborilgan vaqt')
    is_processed = models.BooleanField(default=False, verbose_name='Ko\'rib chiqilgan')
    
    class Meta:
        verbose_name = 'Kontakt forma'
        verbose_name_plural = 'Kontakt formalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.phone} ({self.created_at.strftime('%d.%m.%Y')})"