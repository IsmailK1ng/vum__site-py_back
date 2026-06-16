"""Удаление файлов с диска при изменении/удалении объектов.

Django по дефолту не удаляет файл из storage, когда:
1. ImageField на объекте заменяют — старый файл остаётся orphan'ом.
2. Объект удаляют целиком — все файлы остаются.

Этот модуль регистрирует pre_save и post_delete сигналы для всех моделей
с ImageField, чтобы старые файлы убирались сами.

Старые orphan-файлы, накопившиеся до этого, тут НЕ трогаем — для них
можно сделать management-команду отдельно.
"""

from django.db.models import ImageField
from django.db.models.signals import pre_save, post_delete


def _get_image_field_names(model):
    """Имена всех ImageField модели."""
    return [
        f.name
        for f in model._meta.get_fields()
        if isinstance(f, ImageField)
    ]


def _safe_delete(file_field):
    """Удалить файл из storage без поднятия save() в БД.
    storage.delete() сам справится если файла уже нет на диске.
    """
    if file_field and file_field.name:
        file_field.delete(save=False)


def register_image_cleanup(model):
    """Подключает сигналы для одной модели — на все её ImageField."""
    image_fields = _get_image_field_names(model)
    if not image_fields:
        return

    def on_pre_save(sender, instance, **kwargs):
        # Новый объект — нечего удалять
        if not instance.pk:
            return
        # Старая версия из БД для сравнения
        try:
            old = sender.objects.only(*image_fields).get(pk=instance.pk)
        except sender.DoesNotExist:
            return
        for fname in image_fields:
            old_file = getattr(old, fname, None)
            new_file = getattr(instance, fname, None)
            old_name = old_file.name if old_file else ''
            new_name = new_file.name if new_file else ''
            if old_name and old_name != new_name:
                _safe_delete(old_file)

    def on_post_delete(sender, instance, **kwargs):
        for fname in image_fields:
            _safe_delete(getattr(instance, fname, None))

    # weak=False — иначе локальные closure-функции соберёт GC и сигнал отвалится
    pre_save.connect(on_pre_save, sender=model, weak=False,
                     dispatch_uid=f'image_cleanup_pre_save_{model.__name__}')
    post_delete.connect(on_post_delete, sender=model, weak=False,
                        dispatch_uid=f'image_cleanup_post_delete_{model.__name__}')


def register_all():
    """Регистрация для всех моделей проекта с ImageField.
    Импорт моделей внутри функции — apps.ready() вызывает это уже после загрузки.
    """
    from .models import (
        News, NewsBlock,
        Product, ProductGallery,
        Dealer, DealerProfile,
        TeamMember, SocialLink,
        Promotion, PageMeta,
        BotBroadcast,
        SparePartImage,
    )

    models = [
        News, NewsBlock,
        Product, ProductGallery,
        Dealer, DealerProfile,
        TeamMember, SocialLink,
        Promotion, PageMeta,
        BotBroadcast,
        SparePartImage,
    ]
    for m in models:
        register_image_cleanup(m)
