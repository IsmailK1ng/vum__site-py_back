# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0003_add_missing_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('title_ru', models.CharField(max_length=255, null=True, verbose_name='Заголовок')),
                ('title_en', models.CharField(max_length=255, null=True, verbose_name='Заголовок')),
                ('title_uz', models.CharField(max_length=255, null=True, verbose_name='Заголовок')),
                ('desc', models.TextField(max_length=500, verbose_name='Краткое описание')),
                ('desc_ru', models.TextField(max_length=500, null=True, verbose_name='Краткое описание')),
                ('desc_en', models.TextField(max_length=500, null=True, verbose_name='Краткое описание')),
                ('desc_uz', models.TextField(max_length=500, null=True, verbose_name='Краткое описание')),
                ('author_photo', models.ImageField(blank=True, null=True, upload_to='authors/', verbose_name='Фото автора')),
                ('preview_image', models.ImageField(blank=True, null=True, upload_to='news/previews/', verbose_name='Главное фото')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
            ],
            options={
                'verbose_name': '[UZ] Новость',
                'verbose_name_plural': '[UZ] Новости',
            },
        ),
        migrations.CreateModel(
            name='ContactForm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Имя')),
                ('region', models.CharField(choices=[('Toshkent shahri', 'Toshkent shahri'), ('Andijon viloyati', 'Andijon viloyati'), ('Buxoro viloyati', 'Buxoro viloyati'), ('Fargʻona viloyati', 'Fargʻona viloyati'), ('Jizzax viloyati', 'Jizzax viloyati'), ('Xorazm viloyati', 'Xorazm viloyati'), ('Namangan viloyati', 'Namangan viloyati'), ('Navoiy viloyati', 'Navoiy viloyati'), ('Qashqadaryo viloyati', 'Qashqadaryo viloyati'), ('Samarqand viloyati', 'Samarqand viloyati'), ('Sirdaryo viloyati', 'Sirdaryo viloyati'), ('Surxondaryo viloyati', 'Surxondaryo viloyati'), ('Toshkent viloyati', 'Toshkent viloyati'), ('Qoraqalpogʻiston Respublikasi', 'Qoraqalpogʻiston Respublikasi')], max_length=100, verbose_name='Регион')),
                ('phone', models.CharField(max_length=50, verbose_name='Телефон')),
                ('message', models.TextField(verbose_name='Сообщение')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время отправки')),
                ('status', models.CharField(choices=[('new', 'Новая'), ('in_process', 'В процессе'), ('done', 'Обработана')], default='new', max_length=20, verbose_name='Статус')),
                ('priority', models.CharField(choices=[('high', 'Высокий'), ('medium', 'Средний'), ('low', 'Низкий')], default='medium', max_length=10, verbose_name='Приоритет')),
                ('is_processed', models.BooleanField(default=False, verbose_name='Просмотрено (устарело)')),
                ('admin_comment', models.TextField(blank=True, null=True, verbose_name='Комментарий администратора')),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uz_contacts', to=settings.AUTH_USER_MODEL, verbose_name='Менеджер')),
            ],
            options={
                'verbose_name': '[UZ] Заявка',
                'verbose_name_plural': '[UZ] Заявки',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NewsBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('block_type', models.CharField(choices=[('text', 'Текст'), ('image', 'Изображение'), ('youtube', 'YouTube видео'), ('video', 'Видео файл')], max_length=10, verbose_name='Тип блока')),
                ('text', models.TextField(blank=True, null=True, verbose_name='Текст')),
                ('text_ru', models.TextField(blank=True, null=True, verbose_name='Текст')),
                ('text_en', models.TextField(blank=True, null=True, verbose_name='Текст')),
                ('text_uz', models.TextField(blank=True, null=True, verbose_name='Текст')),
                ('image', models.ImageField(blank=True, null=True, upload_to='news/images/', verbose_name='Фото')),
                ('youtube_url', models.URLField(blank=True, null=True, verbose_name='YouTube ссылка')),
                ('video_file', models.FileField(blank=True, null=True, upload_to='news/videos/', verbose_name='Видео файл')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('news', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='main.news', verbose_name='Новость')),
            ],
            options={
                'verbose_name': '[UZ] Блок новости',
                'verbose_name_plural': '[UZ] Блоки новостей',
                'ordering': ['order'],
            },
        ),
    ]