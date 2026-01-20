# main/serializers.py

from rest_framework import serializers
import logging

logger = logging.getLogger('django')
from main.serializers_base import LanguageSerializerMixin

from .models import (
    News, NewsBlock, ContactForm, JobApplication, 
    Product, FeatureIcon, ProductCardSpec, ProductParameter, ProductFeature, ProductGallery,  
    DealerService, Dealer, BecomeADealerPage, BecomeADealerApplication,
    Vacancy, Promotion, VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate
)


# ========== НОВОСТИ ==========

class NewsBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsBlock
        fields = '__all__'


class NewsSerializer(serializers.ModelSerializer):
    blocks = NewsBlockSerializer(many=True, read_only=True)

    class Meta:
        model = News
        fields = '__all__'


# ========== ЗАЯВКИ ==========

class ContactFormSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    
    class Meta:
        model = ContactForm
        fields = [
            'id', 'name', 'phone', 'region', 'region_display', 
            'product', 'referer', 'utm_data', 'visitor_uid', 
            'message', 'status', 'status_display', 
            'priority', 'priority_display',
            'manager', 'manager_name', 'admin_comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'status_display', 'priority_display', 'region_display']
    
    def validate_referer(self, value):
        """Валидация referer - может быть пустым или относительным URL"""
        if value and len(value) > 500:
            raise serializers.ValidationError("Referer слишком длинный (макс 500 символов)")
        return value
    
    def validate_visitor_uid(self, value):
        """Валидация visitor_uid от amoCRM Pixel"""
        if value:
            if not (value.replace('-', '').replace('_', '').isalnum() and len(value) <= 100):
                raise serializers.ValidationError("Невалидный visitor_uid")
        return value
    
    def validate_utm_data(self, value):
        """Валидация utm_data - может быть строкой или объектом"""
        if value:
            if isinstance(value, dict):
                # Преобразуем объект в JSON строку
                import json
                return json.dumps(value, ensure_ascii=False)
            elif isinstance(value, str):
                # Проверяем что это валидный JSON если это объект в строке
                if value.strip().startswith('{'):
                    try:
                        import json
                        json.loads(value)
                    except json.JSONDecodeError:
                        raise serializers.ValidationError("utm_data должно быть валидным JSON")
                return value
        return value
    
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
        
        contact_form = super().create(validated_data)
        return contact_form


class JobApplicationSerializer(serializers.ModelSerializer):
    """Заявки на вакансии с валидацией резюме"""
    vacancy_title = serializers.CharField(source='vacancy.title', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = ['id', 'vacancy', 'vacancy_title', 'region', 'resume', 'created_at']
        read_only_fields = ['id', 'created_at', 'vacancy_title']
    
    def validate_resume(self, value):
        """Валидация файла резюме"""
        try:
            # Проверка размера (10 MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("Fayl hajmi juda katta. Maksimal 10 MB")
            
            # Проверка формата
            allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
            file_ext = value.name.lower().split('.')[-1]
            if file_ext not in allowed_extensions:
                raise serializers.ValidationError("Noto'g'ri fayl formati. PDF, DOC, DOCX, JPG yoki PNG foydalaning")
            
            return value
        
        except serializers.ValidationError:
            raise  # Пробрасываем ValidationError
        except Exception as e:
            logger.error(f"Критическая ошибка валидации резюме: {str(e)}", exc_info=True)
            raise serializers.ValidationError("Xatolik yuz berdi")


# ========== ПРОДУКТЫ ==========

class FeatureIconSerializer(serializers.ModelSerializer):
    """Иконки для характеристик"""
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = FeatureIcon
        fields = ['id', 'name', 'icon_url']

    def get_icon_url(self, obj):
        request = self.context.get('request')
        if obj.icon:
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url
        return None


class ProductCardSpecSerializer(serializers.ModelSerializer):
    """4 характеристики для карточки продукта"""
    icon = FeatureIconSerializer(read_only=True)
    
    class Meta:
        model = ProductCardSpec
        fields = ['id', 'icon', 'value', 'order']


class ProductCardSerializer(LanguageSerializerMixin, serializers.ModelSerializer):  # ← ДОБАВЬ!
    """Карточки продуктов для списка"""
    card_specs = ProductCardSpecSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    all_categories = serializers.SerializerMethodField()
    
    title = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'category', 'category_display',
            'all_categories',  
            'image_url', 'card_specs', 'is_featured', 'order'
        ]
    def get_title(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'title_{lang}', None) or obj.title
    
    def get_all_categories(self, obj):
        """Возвращает все категории продукта (основную + дополнительные)"""
        categories = [obj.category]  
        
        # Добавляем дополнительные
        if obj.categories:
            additional = [cat.strip() for cat in obj.categories.split(',') if cat.strip()]
            categories.extend(additional)
        
        # Убираем дубликаты
        categories = list(dict.fromkeys(categories))
        
        # Возвращаем с названиями
        result = []
        for cat_slug in categories:
            for slug, name in Product.CATEGORY_CHOICES:
                if slug == cat_slug:
                    result.append({'slug': slug, 'name': name})
                    break
        
        return result
    
    def get_image_url(self, obj):
        """Возвращает URL изображения для карточки"""
        image = obj.card_image if obj.card_image else obj.main_image
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.url)
            return image.url
        return None


class ProductFeatureSerializer(LanguageSerializerMixin, serializers.ModelSerializer):
    """8 характеристик с иконками"""
    icon = FeatureIconSerializer(read_only=True)
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductFeature
        fields = ['id', 'icon', 'name', 'order']
    
    def get_name(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'name_{lang}', None) or obj.name


class ProductGallerySerializer(serializers.ModelSerializer):
    """Галерея продукта"""
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


class ProductDetailSerializer(LanguageSerializerMixin, serializers.ModelSerializer):
    """Детальная страница продукта"""
    card_specs = ProductCardSpecSerializer(many=True, read_only=True)
    spec_groups = serializers.SerializerMethodField()
    features = ProductFeatureSerializer(many=True, read_only=True)
    gallery = ProductGallerySerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    card_image_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    title = serializers.SerializerMethodField()
    
   
    all_categories = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'category', 'category_display',
            'all_categories', 
            'main_image_url', 'card_image_url',
            'card_specs', 'spec_groups', 'features', 'gallery',
            'is_active', 'is_featured', 'order'
        ]
    
    def get_all_categories(self, obj):
        """Возвращает все категории продукта с переводами"""
        language = self.get_current_language()
        
        # Получаем все категории
        categories = [obj.category]
        if obj.categories:
            additional = [cat.strip() for cat in obj.categories.split(',') if cat.strip()]
            categories.extend(additional)
        
        # Убираем дубликаты
        categories = list(dict.fromkeys(categories))
        
        # Возвращаем с названиями на нужном языке
        result = []
        for cat_slug in categories:
            for slug, name in Product.CATEGORY_CHOICES:
                if slug == cat_slug:
                    # Здесь можно добавить переводы названий категорий если нужно
                    result.append({'slug': slug, 'name': name})
                    break
        
        return result
    
    def get_title(self, obj):
        lang = self.get_current_language()  
        return getattr(obj, f'title_{lang}', None) or obj.title
    
    def get_spec_groups(self, obj):
        language = self.get_current_language()
        
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
    
# ========== СЕРИАЛИЗАТОР ДЛЯ ВАКАНСИЙ ==========

class VacancySerializer(LanguageSerializerMixin, serializers.ModelSerializer):
    """Вакансии с поддержкой переводов"""
    title = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()
    contact_info = serializers.SerializerMethodField()
    responsibilities = serializers.SerializerMethodField()
    requirements = serializers.SerializerMethodField()
    conditions = serializers.SerializerMethodField()
    ideal_candidates = serializers.SerializerMethodField()
    
    class Meta:
        model = Vacancy
        fields = [
            'id', 'title', 'short_description', 'contact_info',
            'responsibilities', 'requirements', 'conditions', 'ideal_candidates',
            'is_active', 'created_at'
        ]
    
    def get_title(self, obj):
        lang = self.get_current_language()  
        return getattr(obj, f'title_{lang}', None) or obj.title
    
    def get_short_description(self, obj):
        lang = self.get_current_language()  
        return getattr(obj, f'short_description_{lang}', None) or obj.short_description or ''
    
    def get_contact_info(self, obj):
        lang = self.get_current_language()  
        return getattr(obj, f'contact_info_{lang}', None) or obj.contact_info or ''
    
    def get_responsibilities(self, obj):
        lang = self.get_current_language()  
        responsibilities = obj.responsibilities.all().order_by('order')
        return [
            {
                'id': item.id, 
                'title': getattr(item, f'title_{lang}', None) or item.title or '', 
                'text': getattr(item, f'text_{lang}', None) or item.text or ''
            } 
            for item in responsibilities
        ]
    
    def get_requirements(self, obj):
        lang = self.get_current_language()  
        requirements = obj.requirements.all().order_by('order')
        return [
            {
                'id': item.id, 
                'text': getattr(item, f'text_{lang}', None) or item.text or ''
            } 
            for item in requirements
        ]
    
    def get_conditions(self, obj):
        lang = self.get_current_language()  
        conditions = obj.conditions.all().order_by('order')
        return [
            {
                'id': item.id, 
                'text': getattr(item, f'text_{lang}', None) or item.text or ''
            } 
            for item in conditions
        ]
    
    def get_ideal_candidates(self, obj):
        lang = self.get_current_language()  
        candidates = obj.ideal_candidates.all().order_by('order')
        return [
            {
                'id': item.id, 
                'text': getattr(item, f'text_{lang}', None) or item.text or ''
            } 
            for item in candidates
        ]

from .models import Promotion
from main.serializers_base import LanguageSerializerMixin

class PromotionSerializer(LanguageSerializerMixin, serializers.ModelSerializer):
    """Сериализатор акций с поддержкой языков"""
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    button_text = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'title', 'description', 'image_url', 
            'link', 'button_text', 'priority', 'start_date', 'end_date'
        ]
    
    def get_title(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'title_{lang}', None) or obj.title
    
    def get_description(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'description_{lang}', None) or obj.description
    
    def get_button_text(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'button_text_{lang}', None) or obj.button_text
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None