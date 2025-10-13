# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0009_kgvehicle_category'),
    ]

    operations = [
        # Сначала удаляем unique_together
        migrations.AlterUniqueTogether(
            name='kgvehiclefeature',
            unique_together=set(),
        ),
        
        # Потом удаляем модели
        migrations.DeleteModel(
            name='KGVehicleFeature',
        ),
        migrations.DeleteModel(
            name='FeatureIcon',
        ),
        
        # Обновляем KGFeedback
        migrations.RemoveField(
            model_name='kgfeedback',
            name='is_processed',
        ),
        migrations.AddField(
            model_name='kgfeedback',
            name='status',
            field=models.CharField(
                choices=[('new', 'Новая'), ('in_process', 'В процессе'), ('done', 'Обработана')],
                default='new',
                max_length=20,
                verbose_name='Статус'
            ),
        ),
        migrations.AddField(
            model_name='kgfeedback',
            name='priority',
            field=models.CharField(
                choices=[('high', 'Высокий'), ('medium', 'Средний'), ('low', 'Низкий')],
                default='medium',
                max_length=10,
                verbose_name='Приоритет'
            ),
        ),
        migrations.AddField(
            model_name='kgfeedback',
            name='manager',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='kg_feedbacks',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Ответственный'
            ),
        ),
        
        # Обновляем Meta
        migrations.AlterModelOptions(
            name='kgfeedback',
            options={'ordering': ['-created_at'], 'verbose_name': 'Заявка', 'verbose_name_plural': 'Заявки'},
        ),
        migrations.AlterModelOptions(
            name='kgvehicle',
            options={'ordering': ['-created_at'], 'verbose_name': 'Машина', 'verbose_name_plural': 'Каталог машин'},
        ),
    ]