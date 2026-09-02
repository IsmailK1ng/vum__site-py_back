"""Валидаторы для main-приложения."""

import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Общий лимит размера для пользовательских изображений по всему сайту.
# 5 МБ — баланс между качеством JPEG/PNG большого разрешения
# и нагрузкой на хранение/трафик.
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# Лимит для видео/GIF в рассылках бота — 10 МБ по требованию заказчика
# (не ограничение самого Telegram Bot API, тот пускает заметно больше).
MAX_BROADCAST_VIDEO_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_BROADCAST_VIDEO_EXTENSIONS = ('.mp4', '.mov', '.gif')


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


def validate_broadcast_video(file):
    """Видео/GIF для рассылки бота — не больше 10 МБ, формат mp4/mov/gif.

    Используется как `validators=[validate_broadcast_video]` на FileField
    (не ImageField — Pillow не умеет валидировать видео).
    """
    if not file:
        return

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_BROADCAST_VIDEO_EXTENSIONS:
        raise ValidationError(
            _('Допустимые форматы: %(exts)s.'),
            params={'exts': ', '.join(ALLOWED_BROADCAST_VIDEO_EXTENSIONS)},
            code='invalid_extension',
        )

    if file.size > MAX_BROADCAST_VIDEO_SIZE_BYTES:
        raise ValidationError(
            _('Размер файла не должен превышать 10 МБ. Текущий размер: %(size).2f МБ.'),
            params={'size': file.size / (1024 * 1024)},
            code='file_too_large',
        )
