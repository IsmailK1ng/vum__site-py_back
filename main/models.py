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

    name = models.CharField(max_length=255, verbose_name='Имя')
    region = models.CharField(max_length=100, choices=REGION_CHOICES, verbose_name='Регион')
    phone = models.CharField(max_length=50, verbose_name='Телефон')
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время отправки')
    is_processed = models.BooleanField(default=False, verbose_name='Просмотрено')
    admin_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий администратора')

    class Meta:
        verbose_name = '[UZ] Заявка'
        verbose_name_plural = '[UZ] Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.phone} ({self.created_at.strftime('%d.%m.%Y')})"
    

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
    
    vacancy = models.ForeignKey(
        'Vacancy',
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Вакансия'
    )
    region = models.CharField(max_length=100, choices=REGION_CHOICES, verbose_name='Регион')
    resume = models.FileField(
        upload_to='resumes/%Y/%m/',
        verbose_name='Резюме',
        help_text='Форматы: PDF, DOC, DOCX, JPG, PNG. Максимум 10 MB'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подачи')
    is_processed = models.BooleanField(default=False, verbose_name='Рассмотрено')
    admin_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий HR')
    
    # Дополнительные поля
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

class Vacancy(models.Model):
    """Вакансии компании"""
    title = models.CharField(max_length=255, verbose_name='Название вакансии')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='URL-имя')
    short_description = models.TextField(
        max_length=500, 
        blank=True, 
        verbose_name='Краткое описание',
        help_text='Отображается под заголовком'
    )
    
    # Контактная информация с дефолтным значением
    contact_info = models.TextField(
        verbose_name='Контактная информация',
        default='Присылайте своё резюме на <a href="https://hh.uz" target="_blank">hh.uz</a> или на корпоративную почту <a href="mailto:info@faw.uz">info@faw.uz</a> или <a href="tel:+998555086060">+998(55)508-60-60</a>, отражая опыт: конкретных достижений в продажах, развитии дилерской сети, маркетинге; опыта стратегического планирования и управления командой; успешно реализованных проектов (желательно с цифрами).',
        help_text='Можно использовать HTML'
    )
    
    # Служебные поля
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
        """Количество заявок на эту вакансию"""
        return self.applications.count()

class VacancyResponsibility(models.Model):
    """Обязанности для вакансии"""
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='responsibilities', verbose_name='Вакансия')
    title = models.CharField(max_length=255, verbose_name='Заголовок', blank=True, help_text='Например: Разработка стратегии')
    text = models.TextField(verbose_name='Описание', help_text='Подробное описание обязанности')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Обязанность'
        verbose_name_plural = 'Обязанности'
        ordering = ['order']

    def __str__(self):
        return self.title or self.text[:50]


class VacancyRequirement(models.Model):
    """Требования к кандидату"""
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='requirements', verbose_name='Вакансия')
    text = models.CharField(max_length=500, verbose_name='Требование', help_text='Например: Высшее образование (экономика)')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Требование'
        verbose_name_plural = 'Требования'
        ordering = ['order']

    def __str__(self):
        return self.text[:50]


class VacancyCondition(models.Model):
    """Условия работы"""
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='conditions', verbose_name='Вакансия')
    text = models.CharField(max_length=500, verbose_name='Условие', help_text='Например: Конкурентная зарплата + бонусы')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Условие работы'
        verbose_name_plural = 'Условия работы'
        ordering = ['order']

    def __str__(self):
        return self.text[:50]
        return f"{self.vehicle.title} - {self.value_ru}"
    
    def get_value(self, lang='ru'):
        """Получить значение на нужном языке"""
        if lang == 'en':
            return self.value_en or self.value_ru
        elif lang == 'ky':
            return self.value_ky or self.value_ru
        return self.value_ru


class VacancyIdealCandidate(models.Model):
    """Портрет идеального кандидата"""
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='ideal_candidates', verbose_name='Вакансия')
    text = models.CharField(max_length=500, verbose_name='Качество/Требование', help_text='Например: Высшее образование')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Портрет кандидата'
        verbose_name_plural = 'Портрет идеального кандидата'
        ordering = ['order']

    def __str__(self):
        return self.text[:50]
    