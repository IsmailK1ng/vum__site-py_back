from rest_framework import serializers
from .models import News, NewsBlock


class NewsBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsBlock
        fields = ('id', 'block_type', 'text', 'image', 'youtube_url', 'video_file', 'order')


class NewsSerializer(serializers.ModelSerializer):
    blocks = NewsBlockSerializer(many=True, read_only=True)

    class Meta:
        model = News
        fields = (
            'id',
            'title',
            'desc',
            'author',
            'author_photo',
            'preview_image',
            'created_at',
            'blocks',  # ← вот это добавили
        )