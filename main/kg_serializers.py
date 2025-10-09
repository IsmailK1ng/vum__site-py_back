# main/kg_serializers.py
from rest_framework import serializers
from .models import KGVehicle, KGVehicleImage, KGVehicleFeature, FeatureIcon, KGFeedback


class FeatureIconSerializer(serializers.ModelSerializer):
    """Сериализатор для иконок особенностей"""
    class Meta:
        model = FeatureIcon
        fields = ['id', 'name', 'image']


class KGVehicleImageSerializer(serializers.ModelSerializer):
    """Сериализатор для дополнительных изображений"""
    class Meta:
        model = KGVehicleImage
        fields = ['id', 'image', 'alt', 'order']


class KGVehicleFeatureSerializer(serializers.ModelSerializer):
    """Сериализатор для особенностей машины"""
    feature = FeatureIconSerializer(read_only=True)
    
    class Meta:
        model = KGVehicleFeature
        fields = ['id', 'feature']


class KGVehicleListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка машин (каталог)"""
    class Meta:
        model = KGVehicle
        fields = ['id', 'slug', 'title', 'preview_image', 'is_active']
    
    def to_representation(self, instance):
        """Автоматически возвращаем контент на нужном языке"""
        data = super().to_representation(instance)
        
        # Получаем язык из запроса (например: ?lang=ky)
        request = self.context.get('request')
        lang = request.query_params.get('lang', 'ru') if request else 'ru'
        
        # Подставляем переведенные поля
        title_field = f'title_{lang}'
        slug_field = f'slug_{lang}'
        
        data['title'] = getattr(instance, title_field, instance.title) or instance.title
        data['slug'] = getattr(instance, slug_field, instance.slug) or instance.slug
        
        return data


class KGVehicleDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор машины (для страницы vehicle-details)"""
    vehicle_features = KGVehicleFeatureSerializer(many=True, read_only=True)
    mini_images = KGVehicleImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = KGVehicle
        fields = [
            'id', 'slug', 'title', 'preview_image', 'main_image', 
            'specs', 'vehicle_features', 'mini_images', 'is_active'
        ]
    
    def to_representation(self, instance):
        """Возвращаем данные на нужном языке"""
        data = super().to_representation(instance)
        
        request = self.context.get('request')
        lang = request.query_params.get('lang', 'ru') if request else 'ru'
        
        # Переводим основные поля
        title_field = f'title_{lang}'
        slug_field = f'slug_{lang}'
        specs_field = f'specs_{lang}'
        
        data['title'] = getattr(instance, title_field, instance.title) or instance.title
        data['slug'] = getattr(instance, slug_field, instance.slug) or instance.slug
        data['specs'] = getattr(instance, specs_field, instance.specs) or instance.specs or {}
        
        return data


class KGFeedbackSerializer(serializers.ModelSerializer):
    """Сериализатор для заявок с сайта"""
    vehicle_title = serializers.CharField(source='vehicle.title', read_only=True)
    
    class Meta:
        model = KGFeedback
        fields = [
            'id', 'name', 'phone', 'region', 'vehicle', 'vehicle_title',
            'message', 'created_at', 'is_processed'
        ]
        read_only_fields = ['id', 'created_at', 'is_processed']
    
    def validate_phone(self, value):
        """Валидация номера телефона"""
        if not value.startswith('+996'):
            raise serializers.ValidationError('Номер должен начинаться с +996')
        if len(value) != 13:  # +996 + 9 цифр
            raise serializers.ValidationError('Неверный формат номера телефона')
        return value


class KGFeedbackCreateSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для создания заявки с фронтенда"""
    class Meta:
        model = KGFeedback
        fields = ['name', 'phone', 'region', 'vehicle', 'message']