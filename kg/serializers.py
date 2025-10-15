from rest_framework import serializers
from .models import KGVehicle, KGVehicleImage, KGFeedback, VehicleCardSpec, KGHeroSlide


class VehicleCardSpecSerializer(serializers.ModelSerializer):
    """Сериализатор для характеристик карточки"""
    value = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleCardSpec
        fields = ['id', 'icon', 'value', 'order']
    
    def get_value(self, obj):
        """Получить значение на языке запроса"""
        request = self.context.get('request')
        lang = request.query_params.get('lang', 'ru') if request else 'ru'
        return obj.get_value(lang)


class KGVehicleImageSerializer(serializers.ModelSerializer):
    """Сериализатор для дополнительных изображений"""
    class Meta:
        model = KGVehicleImage
        fields = ['id', 'image', 'alt', 'order']


class KGVehicleListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка машин (каталог)"""
    card_specs = VehicleCardSpecSerializer(many=True, read_only=True)
    
    class Meta:
        model = KGVehicle
        fields = ['id', 'slug', 'title', 'preview_image', 'card_specs', 'is_active']
    
    def to_representation(self, instance):
        """Автоматически возвращаем контент на нужном языке"""
        data = super().to_representation(instance)
        
        request = self.context.get('request')
        lang = request.query_params.get('lang', 'ru') if request else 'ru'
        
        data['title'] = instance.get_title(lang)
        data['slug'] = instance.get_slug(lang)
        
        return data


class KGVehicleDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор машины (для страницы vehicle-details)"""
    mini_images = KGVehicleImageSerializer(many=True, read_only=True)
    card_specs = VehicleCardSpecSerializer(many=True, read_only=True)
    specs = serializers.SerializerMethodField()
    
    class Meta:
        model = KGVehicle
        fields = [
            'id', 'slug', 'title', 'preview_image', 'main_image', 
            'specs', 'mini_images', 'card_specs', 'is_active'
        ]
    def get_specs(self, obj):
        """Получить характеристики на нужном языке"""
        request = self.context.get('request')
        lang = request.GET.get('lang', 'ru') if request else 'ru'
        
        # Получаем спеки на нужном языке
        if lang == 'en':
            return obj.specs_en or obj.specs_ru or {}
        elif lang == 'ky':
            return obj.specs_ky or obj.specs_ru or {}
        return obj.specs_ru or {}


class KGVehicleSerializer(serializers.ModelSerializer):
    """Базовый сериализатор машины"""
    title = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    specs = serializers.SerializerMethodField()
    card_specs = VehicleCardSpecSerializer(many=True, read_only=True)
    mini_images = KGVehicleImageSerializer(many=True, read_only=True)

    class Meta:
        model = KGVehicle
        fields = [
            'id', 'slug', 'title', 'preview_image', 'main_image',
            'specs', 'card_specs', 'mini_images', 'is_active'
        ]

    def get_title(self, obj):
        request = self.context.get('request')
        lang = request.GET.get('lang', 'ru') if request else 'ru'
        return obj.get_title(lang)

    def get_slug(self, obj):
        request = self.context.get('request')
        lang = request.GET.get('lang', 'ru') if request else 'ru'
        return obj.get_slug(lang)

    def get_specs(self, obj):
        request = self.context.get('request')
        lang = request.GET.get('lang', 'ru') if request else 'ru'
        return obj.get_specs(lang) or {}


class KGFeedbackSerializer(serializers.ModelSerializer):
    """Сериализатор для заявок с сайта"""
    vehicle_title = serializers.SerializerMethodField()
    
    class Meta:
        model = KGFeedback
        fields = [
            'id', 'name', 'phone', 'region', 'vehicle', 'vehicle_title',
            'message', 'status', 'priority', 'manager', 'created_at', 'admin_comment'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_vehicle_title(self, obj):
        """Получить название машины на языке запроса"""
        if not obj.vehicle:
            return None
        
        request = self.context.get('request')
        lang = request.query_params.get('lang', 'ru') if request else 'ru'
        
        return obj.vehicle.get_title(lang)
    
    def validate_phone(self, value):
        """Валидация номера телефона"""
        if not value.startswith('+996'):
            raise serializers.ValidationError('Номер должен начинаться с +996')
        if len(value) != 13:
            raise serializers.ValidationError('Неверный формат номера телефона')
        return value


class KGFeedbackCreateSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для создания заявки с фронтенда"""
    class Meta:
        model = KGFeedback
        fields = ['name', 'phone', 'region', 'vehicle', 'message']
    
    def validate_phone(self, value):
        """Валидация номера телефона"""
        if not value.startswith('+996'):
            raise serializers.ValidationError('Номер должен начинаться с +996')
        if len(value) != 13:
            raise serializers.ValidationError('Неверный формат номера телефона')
        return value


class KGHeroSlideSerializer(serializers.ModelSerializer):
    vehicle = KGVehicleSerializer(read_only=True)  # ← Использует тот же сериализатор!
    description = serializers.SerializerMethodField()

    class Meta:
        model = KGHeroSlide
        fields = ['id', 'vehicle', 'description', 'order']

    def get_description(self, obj):
        """Получить описание на нужном языке"""
        request = self.context.get('request')
        lang = request.query_params.get('lang', 'ru') if request else 'ru'
        return obj.get_description(lang)