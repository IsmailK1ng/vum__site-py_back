"""Магазин запчастей + лимит размера 5 МБ на все ImageField.

В этой миграции собрано всё, что относится к магазину:
- 3 новые модели: SparePartType, SparePart, SparePartImage
- Поля name/description с переводимостью (modeltranslation добавит name_ru/_uz/_en,
  description_ru/_uz/_en); base поле тоже отражено как blank=True
- validate_image_size добавляется в validators всех существующих ImageField проекта
  (Dealer.logo, News.author_photo и т.д.) — побочный продукт того же раунда работы.
"""

import ckeditor.fields
import django.db.models.deletion
from django.db import migrations, models

import main.validators


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0026_dealerprofile'),
    ]

    operations = [
        # ===== Лимит 5 МБ на существующие ImageField =====
        migrations.AlterField(
            model_name='botbroadcast',
            name='image',
            field=models.ImageField(blank=True, help_text='Опционально — прикрепить фото к рассылке',
                                    null=True, upload_to='bot/broadcasts/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Изображение'),
        ),
        migrations.AlterField(
            model_name='dealer',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='dealers/logos/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Логотип'),
        ),
        migrations.AlterField(
            model_name='news',
            name='author_photo',
            field=models.ImageField(blank=True, null=True, upload_to='authors/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Фото автора'),
        ),
        migrations.AlterField(
            model_name='news',
            name='preview_image',
            field=models.ImageField(blank=True, null=True, upload_to='news/previews/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Главное фото'),
        ),
        migrations.AlterField(
            model_name='newsblock',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='news/images/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Фото'),
        ),
        migrations.AlterField(
            model_name='pagemeta',
            name='og_image',
            field=models.ImageField(blank=True, help_text='Картинка для соцсетей (рекомендуется: 1200x630px)',
                                    null=True, upload_to='seo/og_images/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='OG Image'),
        ),
        migrations.AlterField(
            model_name='product',
            name='card_image',
            field=models.ImageField(blank=True, null=True, upload_to='products/cards/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Изображение для карточки'),
        ),
        migrations.AlterField(
            model_name='product',
            name='main_image',
            field=models.ImageField(upload_to='products/main/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Главное изображение'),
        ),
        migrations.AlterField(
            model_name='product',
            name='slider_image',
            field=models.ImageField(
                blank=True,
                help_text='Рекомендуемый размер: 420x210px. Если не указано, используется main_image',
                null=True, upload_to='products/slider/',
                validators=[main.validators.validate_image_size],
                verbose_name='Изображение для слайдера',
            ),
        ),
        migrations.AlterField(
            model_name='productgallery',
            name='image',
            field=models.ImageField(upload_to='products/gallery/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Изображение'),
        ),
        migrations.AlterField(
            model_name='promotion',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='promotions/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Изображение'),
        ),
        migrations.AlterField(
            model_name='sociallink',
            name='icon',
            field=models.ImageField(
                blank=True,
                help_text='Загружайте только для варианта "Другая". Для известных соцсетей иконка берётся автоматически.',
                null=True, upload_to='socials/',
                validators=[main.validators.validate_image_size],
                verbose_name='Иконка (своя)',
            ),
        ),
        migrations.AlterField(
            model_name='teammember',
            name='photo',
            field=models.ImageField(blank=True, help_text='Рекомендуемый размер: 400×400 px',
                                    null=True, upload_to='team/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Фото'),
        ),
        migrations.AlterField(
            model_name='dealerprofile',
            name='avatar',
            field=models.ImageField(blank=True, help_text='Необязательно. Рекомендуемый размер: 200×200 px',
                                    null=True, upload_to='dealers/avatars/',
                                    validators=[main.validators.validate_image_size],
                                    verbose_name='Аватар'),
        ),

        # ===== Тип запчасти (справочник) =====
        migrations.CreateModel(
            name='SparePartType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True,
                                          help_text='Например: Двигатель, Тормоза, Фильтр',
                                          max_length=100, verbose_name='Название типа')),
                ('name_uz', models.CharField(blank=True,
                                             help_text='Например: Двигатель, Тормоза, Фильтр',
                                             max_length=100, null=True, verbose_name='Название типа')),
                ('name_ru', models.CharField(blank=True,
                                             help_text='Например: Двигатель, Тормоза, Фильтр',
                                             max_length=100, null=True, verbose_name='Название типа')),
                ('name_en', models.CharField(blank=True,
                                             help_text='Например: Двигатель, Тормоза, Фильтр',
                                             max_length=100, null=True, verbose_name='Название типа')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
            ],
            options={
                'verbose_name': 'Магазин — Тип запчасти',
                'verbose_name_plural': 'Магазин — Типы запчастей',
                'ordering': ['name'],
            },
        ),

        # ===== Запчасть =====
        migrations.CreateModel(
            name='SparePart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('part_number', models.CharField(
                    db_index=True,
                    help_text='Уникальный номер запчасти. Например: 1001-AKB-FAW',
                    max_length=100, unique=True, verbose_name='Артикул (номер детали)',
                )),
                ('name', models.CharField(blank=True, help_text='Краткое название запчасти',
                                          max_length=255, verbose_name='Наименование')),
                ('name_uz', models.CharField(blank=True, help_text='Краткое название запчасти',
                                             max_length=255, null=True, verbose_name='Наименование')),
                ('name_ru', models.CharField(blank=True, help_text='Краткое название запчасти',
                                             max_length=255, null=True, verbose_name='Наименование')),
                ('name_en', models.CharField(blank=True, help_text='Краткое название запчасти',
                                             max_length=255, null=True, verbose_name='Наименование')),
                ('description', ckeditor.fields.RichTextField(
                    blank=True,
                    help_text='Подробное описание запчасти (только текст и форматирование, без изображений)',
                    null=True, verbose_name='Описание',
                )),
                ('description_uz', ckeditor.fields.RichTextField(
                    blank=True,
                    help_text='Подробное описание запчасти (только текст и форматирование, без изображений)',
                    null=True, verbose_name='Описание',
                )),
                ('description_ru', ckeditor.fields.RichTextField(
                    blank=True,
                    help_text='Подробное описание запчасти (только текст и форматирование, без изображений)',
                    null=True, verbose_name='Описание',
                )),
                ('description_en', ckeditor.fields.RichTextField(
                    blank=True,
                    help_text='Подробное описание запчасти (только текст и форматирование, без изображений)',
                    null=True, verbose_name='Описание',
                )),
                ('quantity', models.PositiveIntegerField(default=0, verbose_name='Количество на складе')),
                ('price', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Цена (UZS)')),
                ('is_active', models.BooleanField(default=True, verbose_name='В продаже')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('truck', models.ForeignKey(
                    blank=True,
                    help_text='Привязка к модели грузовика. Можно оставить пустым.',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='spare_parts',
                    to='main.product',
                    verbose_name='Грузовик (опционально)',
                )),
                ('type', models.ForeignKey(
                    help_text='Категория запчасти. Можно выбрать существующий тип или ввести новый.',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='parts',
                    to='main.spareparttype',
                    verbose_name='Тип запчасти',
                )),
            ],
            options={
                'verbose_name': 'Магазин — Запчасть',
                'verbose_name_plural': 'Магазин — Запчасти',
                'ordering': ['-created_at'],
            },
        ),

        # ===== Фото запчасти =====
        migrations.CreateModel(
            name='SparePartImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(
                    upload_to='spare-parts/',
                    validators=[main.validators.validate_image_size],
                    verbose_name='Фото',
                )),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('part', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='images',
                    to='main.sparepart',
                    verbose_name='Запчасть',
                )),
            ],
            options={
                'verbose_name': 'Фото запчасти',
                'verbose_name_plural': 'Фото запчастей',
                'ordering': ['order', 'id'],
            },
        ),
    ]
