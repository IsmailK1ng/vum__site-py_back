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
    manager_name = serializers.CharField(source='manager.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    
    class Meta:
        model = ContactForm
        fields = [
            'id', 'name', 'phone', 'region', 'region_display', 
            'product', 
            'referer',  
            'utm_data',  
            'message',
            'status', 'status_display', 'priority', 'priority_display',
            'manager', 'manager_name', 'admin_comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'status_display', 'priority_display', 'region_display']
    
    def create(self, validated_data):
        import json
        from urllib.parse import urlparse, parse_qs
        
        validated_data.setdefault('status', 'new')
        validated_data.setdefault('priority', 'medium')
        
        request = self.context.get('request')
        
        if request:
            if not validated_data.get('referer'):
                referer = request.META.get('HTTP_REFERER')
                if referer:
                    validated_data['referer'] = referer
            
            utm_from_body = validated_data.get('utm_data')
            
            if utm_from_body:
                if isinstance(utm_from_body, str):
                    pass
                elif isinstance(utm_from_body, dict):
                    validated_data['utm_data'] = json.dumps(utm_from_body, ensure_ascii=False)
            else:
                referer = validated_data.get('referer') or request.META.get('HTTP_REFERER')
                
                if referer:
                    parsed = urlparse(referer)
                    query_params = parse_qs(parsed.query)
                    
                    utm_params = {}
                    for key in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']:
                        if key in query_params:
                            utm_params[key] = query_params[key][0]
                    
                    if utm_params:
                        validated_data['utm_data'] = json.dumps(utm_params, ensure_ascii=False)
        
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
    icon_url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = FeatureIcon
        fields = ['id', 'name', 'icon_url']

    def get_name(self, obj):
        return obj.name   # ← фикс

    def get_icon_url(self, obj):
        request = self.context.get('request')
        if obj.icon:
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
        fields = ['id', 'category', 'category_name', 'text', 'order']


class ProductFeatureSerializer(serializers.ModelSerializer):
    """Сериализатор для характеристик с иконками (8 шт)"""
    icon = FeatureIconSerializer(read_only=True)
    name = serializers.SerializerMethodField()  # ← Добавляем перевод name
    
    class Meta:
        model = ProductFeature
        fields = ['id', 'icon', 'name', 'order']
    
    def get_name(self, obj):
        """Возвращаем name на нужном языке"""
        request = self.context.get('request')
        if request:
            path = request.path
            if '/uz/' in path:
                return obj.name_uz or obj.name
            elif '/en/' in path:
                return obj.name_en or obj.name
        return obj.name_ru or obj.name


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
    spec_groups = serializers.SerializerMethodField()
    features = ProductFeatureSerializer(many=True, read_only=True)
    gallery = ProductGallerySerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    card_image_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    title = serializers.SerializerMethodField()  # ← Добавляем перевод названия
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'category', 'category_display',
            'main_image_url', 'card_image_url',
            'card_specs', 'spec_groups', 'features', 'gallery',
            'is_active', 'is_featured', 'order'
        ]
    
    def get_title(self, obj):
        """Возвращаем название продукта на нужном языке"""
        request = self.context.get('request')
        if request:
            path = request.path
            if '/uz/' in path:
                return obj.title_uz or obj.title
            elif '/en/' in path:
                return obj.title_en or obj.title
        return obj.title_ru or obj.title
    
    def get_spec_groups(self, obj):
        """Группируем параметры по категориям с переводом"""
        request = self.context.get('request')
        language = 'ru'
        
        if request:
            path = request.path
            if '/uz/' in path:
                language = 'uz'
            elif '/ru/' in path:
                language = 'ru'
            elif '/en/' in path:
                language = 'en'
        
        CATEGORY_TRANSLATIONS = {
            'ru': {
                'main': 'Основные параметры',
                'engine': 'Двигатель',
                'weight': 'Весовые параметры',
                'transmission': 'Трансмиссия',
                'brakes': 'Система тормозов и шин',
                'comfort': 'Удобства',
                'superstructure': 'Надстройка',
                'cabin': 'Кабина',
                'additional': 'Дополнительные параметры',
            },
            'uz': {
                'main': 'Asosiy parametrlar',
                'engine': 'Dvigatel',
                'weight': 'Og\'irlik parametrlari',
                'transmission': 'Transmissiya',
                'brakes': 'Tormoz va shinalar tizimi',
                'comfort': 'Qulayliklar',
                'superstructure': 'Qo\'shimcha qurilma',
                'cabin': 'Kabina',
                'additional': 'Qo\'shimcha parametrlar',
            },
            'en': {
                'main': 'Main Parameters',
                'engine': 'Engine',
                'weight': 'Weight Parameters',
                'transmission': 'Transmission',
                'brakes': 'Braking System and Tires',
                'comfort': 'Comfort Features',
                'superstructure': 'Superstructure',
                'cabin': 'Cabin',
                'additional': 'Additional Parameters',
            }
        }
        
        parameters = obj.parameters.all().order_by('category', 'order')
        
        grouped = {}
        for param in parameters:
            category = param.category
            category_display = CATEGORY_TRANSLATIONS.get(language, {}).get(
                category, 
                param.get_category_display()
            )
            
            if category not in grouped:
                grouped[category] = {
                    'category_name': category_display,
                    'parameters': []
                }
            
            # Получаем текст параметра на нужном языке
            text_value = getattr(param, f'text_{language}', None) or param.text or ''
            
            grouped[category]['parameters'].append({
                'id': param.id,
                'text': text_value,
                'order': param.order
            })
        
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