from rest_framework import serializers
from .models import KGVehicle, KGVehicleImage, VehicleCardSpec, KGFeedback, KGHeroSlide

# ============================================
# ОБЩИЕ ФУНКЦИИ
# ============================================

def validate_kg_phone(value):
    """Общая валидация телефона Кыргызстана"""
    if not value.startswith('+996'):
        raise serializers.ValidationError('Номер должен начинаться с +996')
    
    clean_phone = value.replace(' ', '')
    if len(clean_phone) != 13:
        raise serializers.ValidationError('Неверный формат номера телефона')
    
    return value

# ============================================
# СЕРИАЛИЗАТОР: ДОПОЛНИТЕЛЬНЫЕ ФОТО
# ============================================

class KGVehicleImageSerializer(serializers.ModelSerializer):
    """Сериализатор для дополнительных фото"""
    class Meta:
        model = KGVehicleImage
        fields = ['id', 'image', 'alt', 'order']


# ============================================
# СЕРИАЛИЗАТОР: ХАРАКТЕРИСТИКИ ДЛЯ КАТАЛОГА
# ============================================

# serializers.py
class VehicleCardSpecSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    
    def get_icon(self, obj):
        if obj.icon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.icon.url)  
            return obj.icon.url
        return None
    
    def get_value(self, obj):
        lang = self.context.get('lang', 'ru')
        

        if lang == 'ky' and not obj.value_ky and obj.value_ru:
            return obj.auto_translate(obj.value_ru, 'ky')
        elif lang == 'en' and not obj.value_en and obj.value_ru:
            return obj.auto_translate(obj.value_ru, 'en')
        
        return obj.get_value(lang)
    
    class Meta:
        model = VehicleCardSpec
        fields = ['id', 'icon', 'value', 'order']


# ============================================
# СЕРИАЛИЗАТОР: ДЕТАЛЬНЫЕ ХАРАКТЕРИСТИКИ
# ============================================

class DetailedSpecsSerializer(serializers.Serializer):
    """Детальные характеристики для страницы детализации"""
    
    # Основные
    general = serializers.SerializerMethodField()
    # Весовые
    weight = serializers.SerializerMethodField()
    # Кузов
    body = serializers.SerializerMethodField()
    # Двигатель
    engine = serializers.SerializerMethodField()
    # Трансмиссия
    transmission = serializers.SerializerMethodField()
    # Шины
    tires = serializers.SerializerMethodField()
    # Кабина
    cabin = serializers.SerializerMethodField()
    
    def get_general(self, obj):
        lang = self.context.get('lang', 'ru')
        data = {}
        
        if obj.wheel_formula:
            data['wheelFormula'] = obj.wheel_formula
        
        if lang == 'en' and obj.dimensions_en:
            data['dimensions'] = obj.dimensions_en
        elif lang == 'ky' and obj.dimensions_ky:
            data['dimensions'] = obj.dimensions_ky
        elif obj.dimensions_ru:
            data['dimensions'] = obj.dimensions_ru
        
        if obj.wheelbase:
            data['wheelbase'] = obj.wheelbase
        
        if lang == 'en' and obj.fuel_type_en:
            data['fuelType'] = obj.fuel_type_en
        elif lang == 'ky' and obj.fuel_type_ky:
            data['fuelType'] = obj.fuel_type_ky
        elif obj.fuel_type_ru:
            data['fuelType'] = obj.fuel_type_ru
        
        if obj.tank_volume:
            data['tankVolume'] = obj.tank_volume
        
        return data if data else None
    
    def get_weight(self, obj):
        data = {}
        
        if obj.curb_weight:
            data['curbWeight'] = obj.curb_weight
        if obj.payload:
            data['payload'] = obj.payload
        if obj.gross_weight:
            data['grossWeight'] = obj.gross_weight
        
        return data if data else None
    
    def get_body(self, obj):
        lang = self.context.get('lang', 'ru')
        data = {}
        
        if lang == 'en' and obj.body_type_en:
            data['type'] = obj.body_type_en
        elif lang == 'ky' and obj.body_type_ky:
            data['type'] = obj.body_type_ky
        elif obj.body_type_ru:
            data['type'] = obj.body_type_ru
        
        if lang == 'en' and obj.body_dimensions_en:
            data['dimensions'] = obj.body_dimensions_en
        elif lang == 'ky' and obj.body_dimensions_ky:
            data['dimensions'] = obj.body_dimensions_ky
        elif obj.body_dimensions_ru:
            data['dimensions'] = obj.body_dimensions_ru
        
        if obj.body_volume:
            data['volume'] = obj.body_volume
        
        if lang == 'en' and obj.body_material_en:
            data['material'] = obj.body_material_en
        elif lang == 'ky' and obj.body_material_ky:
            data['material'] = obj.body_material_ky
        elif obj.body_material_ru:
            data['material'] = obj.body_material_ru
        
        if lang == 'en' and obj.loading_type_en:
            data['loadingType'] = obj.loading_type_en
        elif lang == 'ky' and obj.loading_type_ky:
            data['loadingType'] = obj.loading_type_ky
        elif obj.loading_type_ru:
            data['loadingType'] = obj.loading_type_ru
        
        return data if data else None
    
    def get_engine(self, obj):
        data = {}
        
        if obj.engine_model:
            data['model'] = obj.engine_model
        if obj.engine_volume:
            data['volume'] = obj.engine_volume
        if obj.engine_power:
            data['power'] = obj.engine_power
        
        return data if data else None
    
    def get_transmission(self, obj):
        lang = self.context.get('lang', 'ru')
        data = {}
        
        if obj.transmission_model:
            data['model'] = obj.transmission_model
        
        if lang == 'en' and obj.transmission_type_en:
            data['type'] = obj.transmission_type_en
        elif lang == 'ky' and obj.transmission_type_ky:
            data['type'] = obj.transmission_type_ky
        elif obj.transmission_type_ru:
            data['type'] = obj.transmission_type_ru
        
        if obj.gears:
            data['gears'] = obj.gears
        
        return data if data else None
    
    def get_tires(self, obj):
        lang = self.context.get('lang', 'ru')
        data = {}
        
        if obj.tire_type:
            data['type'] = obj.tire_type
        
        if lang == 'en' and obj.suspension_en:
            data['suspension'] = obj.suspension_en
        elif lang == 'ky' and obj.suspension_ky:
            data['suspension'] = obj.suspension_ky
        elif obj.suspension_ru:
            data['suspension'] = obj.suspension_ru
        
        if lang == 'en' and obj.brakes_en:
            data['brakes'] = obj.brakes_en
        elif lang == 'ky' and obj.brakes_ky:
            data['brakes'] = obj.brakes_ky
        elif obj.brakes_ru:
            data['brakes'] = obj.brakes_ru
        
        return data if data else None
    
    def get_cabin(self, obj):
        lang = self.context.get('lang', 'ru')
        data = {}
        
        if lang == 'en' and obj.cabin_category_en:
            data['category'] = obj.cabin_category_en
        elif lang == 'ky' and obj.cabin_category_ky:
            data['category'] = obj.cabin_category_ky
        elif obj.cabin_category_ru:
            data['category'] = obj.cabin_category_ru
        
        if lang == 'en' and obj.cabin_equipment_en:
            data['equipment'] = obj.cabin_equipment_en
        elif lang == 'ky' and obj.cabin_equipment_ky:
            data['equipment'] = obj.cabin_equipment_ky
        elif obj.cabin_equipment_ru:
            data['equipment'] = obj.cabin_equipment_ru
        
        return data if data else None


# ============================================
# СЕРИАЛИЗАТОР: СПИСОК МАШИН (КАТАЛОГ)
# ============================================

class KGVehicleListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка машин (каталог)"""
    title = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    card_specs = VehicleCardSpecSerializer(many=True, read_only=True)
    category_display = serializers.SerializerMethodField()
    
    def get_title(self, obj):
        lang = self.context.get('lang', 'ru')
        return obj.get_title(lang)
    
    def get_slug(self, obj):
        lang = self.context.get('lang', 'ru')
        return obj.get_slug(lang)
    
    def get_category_display(self, obj):
        return obj.get_category_display()
    
    class Meta:
        model = KGVehicle
        fields = [
            'id', 'slug', 'title', 'category', 'category_display',
            'preview_image', 'card_specs', 'is_active'
        ]


# ============================================
# СЕРИАЛИЗАТОР: ДЕТАЛИЗАЦИЯ МАШИНЫ
# ============================================

class KGVehicleDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной страницы машины"""
    title = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    card_specs = VehicleCardSpecSerializer(many=True, read_only=True)
    gallery_images = KGVehicleImageSerializer(many=True, source='mini_images', read_only=True)
    features = serializers.SerializerMethodField()
    detailed_specs = serializers.SerializerMethodField()
    
    def get_title(self, obj):
        lang = self.context.get('lang', 'ru')
        return obj.get_title(lang)
    
    def get_slug(self, obj):
        lang = self.context.get('lang', 'ru')
        return obj.get_slug(lang)
    
    def get_features(self, obj):
        """Возвращает список активных features"""
        return obj.get_features()
    
    def get_detailed_specs(self, obj):
        lang = self.context.get('lang', 'ru')
        serializer = DetailedSpecsSerializer(obj, context={'lang': lang})
        return serializer.data
    
    class Meta:
        model = KGVehicle
        fields = [
            'id', 'slug', 'title', 'category',
            'preview_image', 'main_image',
            'card_specs', 'gallery_images',
            'features', 'detailed_specs',
            'is_active'
        ]


# ============================================
# СЕРИАЛИЗАТОР: HERO-СЛАЙДЫ
# ============================================

class KGHeroSlideSerializer(serializers.ModelSerializer):
    """Сериализатор для Hero-слайдов"""
    vehicle = KGVehicleDetailSerializer(read_only=True)
    description = serializers.SerializerMethodField()
    
    def get_description(self, obj):
        lang = self.context.get('lang', 'ru')
        return obj.get_description(lang)
    
    class Meta:
        model = KGHeroSlide
        fields = ['id', 'vehicle', 'description', 'order']


# ============================================
# СЕРИАЛИЗАТОР: ЗАЯВКИ (полный)
# ============================================

class KGFeedbackSerializer(serializers.ModelSerializer):
    """Полный сериализатор для админки"""
    vehicle_title = serializers.SerializerMethodField()
    
    class Meta:
        model = KGFeedback
        fields = [
            'id', 'name', 'phone', 'region', 'vehicle', 'vehicle_title',
            'message', 'status', 'priority', 'manager', 'created_at', 'admin_comment'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_vehicle_title(self, obj):
        if obj.vehicle:
            return obj.vehicle.title_ru
        return None


# ============================================
# СЕРИАЛИЗАТОР: СОЗДАНИЕ ЗАЯВКИ (frontend)
# ============================================

class KGFeedbackCreateSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для создания заявки с frontend"""
    
    class Meta:
        model = KGFeedback
        fields = ['name', 'phone', 'region', 'vehicle', 'message']
    
    def validate_phone(self, value):
        return validate_kg_phone(value)
    
    def create(self, validated_data):
        """Создание заявки с дефолтными значениями"""
        return KGFeedback.objects.create(
            **validated_data,
            status='new',  # По умолчанию новая
            priority='medium'  # По умолчанию средний приоритет
        )