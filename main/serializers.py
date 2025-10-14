from rest_framework import serializers
from .models import News, NewsBlock, ContactForm, JobApplication


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


class JobApplicationSerializer(serializers.ModelSerializer):
    vacancy_title = serializers.CharField(source='vacancy.title', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = ['id', 'vacancy', 'vacancy_title', 'region', 'resume', 'created_at']
        read_only_fields = ['id', 'created_at', 'vacancy_title']
    
    def validate_resume(self, value):
        """Валидация файла резюме"""
        # Проверка размера (10 MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Fayl hajmi juda katta. Maksimal 10 MB")
        
        # Проверка формата
        allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
        file_ext = value.name.lower().split('.')[-1]
        if file_ext not in allowed_extensions:
            raise serializers.ValidationError("Noto'g'ri fayl formati. PDF, DOC, DOCX, JPG yoki PNG foydalaning")
        
        return value