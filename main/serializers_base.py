# main/serializers_base.py

from django.utils.translation import get_language


class LanguageSerializerMixin:
    def get_current_language(self):
        return get_language() or 'uz'