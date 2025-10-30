from django.db import migrations


def create_default_services(apps, schema_editor):
    """Создаем 3 базовые услуги для дилеров"""
    DealerService = apps.get_model('main', 'DealerService')
    
    # Используем базовое поле 'name' вместо переводов
    services = [
        {
            'name': "Sotuv bo'limlari",
            'slug': 'sotuv',
            'order': 1,
            'is_active': True
        },
        {
            'name': "Servis markazlari",
            'slug': 'servis',
            'order': 2,
            'is_active': True
        },
        {
            'name': "Ehtiyot qismlar",
            'slug': 'ehtiyot-qismlar',
            'order': 3,
            'is_active': True
        },
    ]
    
    for service_data in services:
        DealerService.objects.get_or_create(
            slug=service_data['slug'],
            defaults=service_data
        )


def remove_default_services(apps, schema_editor):
    """Откат миграции (удаляем услуги)"""
    DealerService = apps.get_model('main', 'DealerService')
    DealerService.objects.filter(
        slug__in=['sotuv', 'servis', 'ehtiyot-qismlar']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_becomeadealerpage_dealerservice_and_more'),
    ]

    operations = [
        migrations.RunPython(create_default_services, remove_default_services),
    ]