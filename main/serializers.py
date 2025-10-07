from rest_framework import serializers
from .models import News, NewsBlock, ContactForm


class NewsBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsBlock
        fields = '__all__'


class NewsSerializer(serializers.ModelSerializer):
    blocks = NewsBlockSerializer(many=True, read_only=True)

    class Meta:
        model = News
        fields = '__all__'

class ContactFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactForm
        fields = ['id', 'name', 'region', 'phone', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']