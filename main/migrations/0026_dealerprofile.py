"""Дилерская учётная запись — модель DealerProfile.

Содержит:
- 1:1 связь с auth.User (логин/пароль через Django auth-бэкенд)
- Имя и аватарка (отображаются в кабинете)
- Юр. данные: company_name, inn, contract_number (обязательны в форме админки,
  но на уровне модели blank=True — чтобы можно было создать заготовку и заполнить позже)
- is_active — управление доступом в кабинет без удаления учётки
"""

import django.core.validators
from django.conf import settings
from django.db import migrations, models

import main.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0025_alter_teammember_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='DealerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    help_text='Название компании или ФИО дилера, отображается в кабинете',
                    max_length=200,
                    verbose_name='Наименование / Имя',
                )),
                ('avatar', models.ImageField(
                    blank=True,
                    help_text='Необязательно. Рекомендуемый размер: 200×200 px',
                    null=True,
                    upload_to='dealers/avatars/',
                    validators=[main.validators.validate_image_size],
                    verbose_name='Аватар',
                )),
                ('company_name', models.CharField(
                    blank=True,
                    help_text='Полное название организации. Например: ООО "Тмыв денег"',
                    max_length=255,
                    verbose_name='Юр. название',
                )),
                ('inn', models.CharField(
                    blank=True,
                    db_index=True,
                    help_text='Только цифры. Например: 304445333',
                    max_length=20,
                    verbose_name='ИНН',
                )),
                ('contract_number', models.CharField(
                    blank=True,
                    help_text='Например: 12345/2026',
                    max_length=100,
                    verbose_name='Номер договора',
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Снимите галку, чтобы заблокировать вход без удаления учётки',
                    verbose_name='Активен',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлён')),
                ('user', models.OneToOneField(
                    on_delete=models.deletion.CASCADE,
                    related_name='dealer_profile',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Учётная запись',
                )),
            ],
            options={
                'verbose_name': 'Дилер (учётная запись)',
                'verbose_name_plural': 'Дилеры — учётные записи',
                'ordering': ['name'],
            },
        ),
    ]
