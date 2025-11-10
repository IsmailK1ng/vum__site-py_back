from rest_framework import serializers
from .models import News, NewsBlock, ContactForm, JobApplication, Product, FeatureIcon,ProductCardSpec, ProductParameter, ProductFeature, ProductGallery,  DealerService, Dealer, BecomeADealerPage, BecomeADealerApplication


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
    """Сериализатор для заявок (обновленный с функционалом из KG)"""
    manager_name = serializers.CharField(source='manager.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    
    class Meta:
        model = ContactForm
        fields = [
            'id', 'name', 'phone', 'region', 'region_display', 'message',
            'status', 'status_display', 'priority', 'priority_display',
            'manager', 'manager_name', 'admin_comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'status_display', 'priority_display', 'region_display']
    
    def create(self, validated_data):
        # Используем setdefault вместо прямого присваивания
        validated_data.setdefault('status', 'new')
        validated_data.setdefault('priority', 'medium')
        return super().create(validated_data)

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
    

# ========== СЕРИАЛИЗАТОРЫ ДЛЯ ПРОДУКТОВ ==========

class FeatureIconSerializer(serializers.ModelSerializer):
    """Сериализатор для иконок характеристик"""
    icon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FeatureIcon
        fields = ['id', 'name', 'icon_url']
    
    def get_icon_url(self, obj):
        if obj.icon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url
        return None


class ProductCardSpecSerializer(serializers.ModelSerializer):
    """Сериализатор для 4 характеристик карточки"""
    icon = FeatureIconSerializer(read_only=True)
    
    class Meta:
        model = ProductCardSpec
        fields = ['id', 'icon', 'value', 'order']


class ProductCardSerializer(serializers.ModelSerializer):
    """Сериализатор для карточек продуктов (список)"""
    card_specs = ProductCardSpecSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'category', 'category_display',
            'image_url', 'card_specs', 'is_featured', 'order'
        ]
    
    def get_image_url(self, obj):
        """Возвращает URL изображения для карточки"""
        image = obj.card_image if obj.card_image else obj.main_image
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.url)
            return image.url
        return None


class ProductParameterSerializer(serializers.ModelSerializer):
    """Сериализатор для параметров"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = ProductParameter
        fields = ['id', 'category', 'category_display', 'text', 'order']


class ProductFeatureSerializer(serializers.ModelSerializer):
    """Сериализатор для характеристик с иконками (8 шт)"""
    icon = FeatureIconSerializer(read_only=True)
    
    class Meta:
        model = ProductFeature
        fields = ['id', 'icon', 'name', 'order']


class ProductGallerySerializer(serializers.ModelSerializer):
    """Сериализатор для галереи"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductGallery
        fields = ['id', 'image_url', 'order']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной страницы продукта"""
    card_specs = ProductCardSpecSerializer(many=True, read_only=True)
    spec_groups = serializers.SerializerMethodField()  # ← Группируем параметры
    features = ProductFeatureSerializer(many=True, read_only=True)
    gallery = ProductGallerySerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    card_image_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'category', 'category_display',
            'main_image_url', 'card_image_url',
            'card_specs', 'spec_groups', 'features', 'gallery',
            'is_active', 'is_featured', 'order'
        ]
    
    def get_spec_groups(self, obj):
        """Группируем параметры по категориям для фронтенда"""
        parameters = obj.parameters.all().order_by('category', 'order')
        
        # Группируем по категориям
        grouped = {}
        for param in parameters:
            category = param.category
            category_display = param.get_category_display()
            
            if category not in grouped:
                grouped[category] = {
                    'category_name': category_display,
                    'parameters': []
                }
            
            grouped[category]['parameters'].append({
                'id': param.id,
                'text': param.text,
                'order': param.order
            })
        
        # Преобразуем в список с правильным порядком категорий
        category_order = ['main', 'engine', 'weight', 'transmission', 'brakes', 'comfort', 'superstructure', 'cabin', 'additional']
        result = []
        for cat in category_order:
            if cat in grouped:
                result.append(grouped[cat])
        
        return result
    
    def get_main_image_url(self, obj):
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None
    
    def get_card_image_url(self, obj):
        if obj.card_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.card_image.url)
            return obj.card_image.url
        return None
# Сериализаторы для дилеров

class DealerServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealerService
        fields = ['id', 'name', 'slug']


class DealerSerializer(serializers.ModelSerializer):
    services = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = Dealer
        fields = [
            'id', 'name', 'city', 'address', 'coordinates',
            'phone', 'email', 'website', 'working_hours',
            'manager', 'services'
        ]
    
    def get_services(self, obj):
        return [service.name for service in obj.services.all()]
    
    def get_coordinates(self, obj):
        return [float(obj.latitude), float(obj.longitude)]


class BecomeADealerPageSerializer(serializers.ModelSerializer):
    requirements = serializers.SerializerMethodField()
    
    class Meta:
        model = BecomeADealerPage
        fields = [
            'title', 'intro_text', 'subtitle', 'important_note',
            'requirements', 'contact_phone', 'contact_email', 'contact_address'
        ]
    
    def get_requirements(self, obj):
        return [req.text for req in obj.requirements.all().order_by('order')]


class BecomeADealerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BecomeADealerApplication
        fields = [
            'name', 'company_name', 'experience_years', 
            'region', 'phone', 'message'
        ]
    
    def create(self, validated_data):
        validated_data['status'] = 'new'
        validated_data['priority'] = 'medium'
        return super().create(validated_data)