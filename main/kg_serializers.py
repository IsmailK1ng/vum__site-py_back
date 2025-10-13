# main/kg_serializers.py
from rest_framework import serializers
from .models import (
    KGVehicle, KGVehicleImage,
    KGFeedback, VehicleCardSpec, KGHeroSlide
)


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
    
    class Meta:
        model = KGVehicle
        fields = [
            'id', 'slug', 'title', 'preview_image', 'main_image', 
            'specs', 'mini_images', 'card_specs', 'is_active'
        ]
    
    def to_representation(self, instance):
        """Возвращаем данные на нужном языке"""
        data = super().to_representation(instance)
        
        request = self.context.get('request')
        lang = request.query_params.get('lang', 'ru') if request else 'ru'
        
        data['title'] = instance.get_title(lang)
        data['slug'] = instance.get_slug(lang)
        data['specs'] = instance.get_specs(lang)
        
        return data


# Добавляем этот сериализатор (он нужен для kg_views.py)
class KGVehicleSerializer(serializers.ModelSerializer):
    """Базовый сериализатор машины"""
    card_specs = VehicleCardSpecSerializer(many=True, read_only=True)
    mini_images = KGVehicleImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = KGVehicle
        fields = '__all__'


class KGHeroSlideSerializer(serializers.ModelSerializer):
    """Сериализатор для Hero-слайдов"""
    vehicle = KGVehicleListSerializer(read_only=True)
    
    class Meta:
        model = KGHeroSlide
        fields = ['id', 'vehicle', 'order']


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