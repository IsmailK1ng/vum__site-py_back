"""Валидаторы для main-приложения."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Общий лимит размера для пользовательских изображений по всему сайту.
# 5 МБ — баланс между качеством JPEG/PNG большого разрешения
# и нагрузкой на хранение/трафик.
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_image_size(file):
    """Запрещает загрузку изображений > 5 МБ.

    Используется как `validators=[validate_image_size]` на ImageField.
    Срабатывает в admin-формах и любых ModelForm-валидациях.
    """
    if file and file.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            _('Размер файла не должен превышать 5 МБ. Текущий размер: %(size).2f МБ.'),
            params={'size': file.size / (1024 * 1024)},
            code='file_too_large',
        )
