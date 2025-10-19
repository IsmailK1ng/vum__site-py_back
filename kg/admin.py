from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from .models import KGVehicle, KGVehicleImage, VehicleCardSpec, KGFeedback, KGHeroSlide, IconTemplate
from .forms import VehicleCardSpecForm  
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime



# ============================================
# INLINE: ХАРАКТЕРИСТИКИ ДЛЯ КАТАЛОГА
# ============================================

class VehicleCardSpecInline(admin.TabularInline):
    model = VehicleCardSpec
    form = VehicleCardSpecForm 
    extra = 1
    fields = ('icon_selector', 'icon_preview', 'value_ru', 'value_ky', 'value_en', 'order')
    readonly_fields = ('icon_selector', 'icon_preview')
    verbose_name = "Характеристика"
    verbose_name_plural = "Характеристики для каталога"

    def icon_preview(self, obj):
        return format_html('<img src="{}" width="50" style="border-radius:8px;">', obj.icon.url) if obj.icon else "—"
    icon_preview.short_description = "Превью"

    def icon_selector(self, obj):
        templates = IconTemplate.objects.all().order_by('order')
        
        if not templates.exists():
            return mark_safe('<p style="color:red;">⚠️ Нет иконок в библиотеке</p>')
        
        html = '''
        <div class="icon-selector-widget">
            <details style="border:1px solid #ddd; border-radius:8px; padding:8px; background:#f9f9f9;">
                <summary style="cursor:pointer; padding:10px; background:#e3f2fd; border-radius:6px; font-weight:600;">
                    Выбрать иконку ({count})
                </summary>
                <div style="padding:10px 0; margin-top:10px;">
                    <div class="icon-grid" style="display:grid; grid-template-columns:repeat(2, 1fr); gap:10px; max-width:220px;">
        '''.format(count=templates.count())
        
        for t in templates:
            html += '''
            <div class="icon-card" 
                data-template-id="{id}"
                data-icon-url="{url}"
                style="text-align:center; padding:8px; border:2px solid #ddd; border-radius:8px; cursor:pointer; background:#fff; transition:all 0.2s;">
                <img src="{url}" width="40" height="40" style="display:block; margin:0 auto 5px;">
                <small style="font-size:9px; color:#666;">{name}</small>
            </div>
            '''.format(id=t.id, url=t.icon.url, name=t.name)
        
        html += '''
                    </div>
                </div>
            </details>
        </div>
        <style>
            .icon-card:hover {
                border-color: #64b5f6 !important;
                transform: scale(1.05);
            }
        </style>
        '''
        
        return mark_safe(html)
    icon_selector.short_description = "Выбор иконки"


# ============================================
# INLINE: ДОПОЛНИТЕЛЬНЫЕ ФОТО
# ============================================

class KGVehicleImageInline(admin.TabularInline):
    model = KGVehicleImage
    extra = 1
    fields = ('image', 'image_preview', 'alt', 'order')
    readonly_fields = ('image_preview',)
    verbose_name = "Дополнительное фото"
    verbose_name_plural = "Дополнительные фото"

    def image_preview(self, obj):
        return format_html('<img src="{}" width="80" style="border-radius:8px;">', obj.image.url) if obj.image else "Не загружено"
    image_preview.short_description = "Превью"


# ============================================
# ADMIN: КАТАЛОГ МАШИН
# ============================================

@admin.register(KGVehicle)
class KGVehicleAdmin(admin.ModelAdmin):
    list_display = ('mini_thumb', 'title_display', 'category_badge', 'is_active', 'created_at', 'action_buttons')
    list_editable = ('is_active',)
    list_filter = ('category', 'is_active', 'created_at')
    list_select_related = True
    search_fields = ('title_ru', 'title_ky', 'title_en', 'slug')
    readonly_fields = ('created_at', 'updated_at', 'category', 'specs_accordion_html')
    list_per_page = 20
    date_hierarchy = 'created_at'
    inlines = [VehicleCardSpecInline, KGVehicleImageInline]

    fieldsets = (
        ('Название техники', {'fields': ('title_ru', 'title_ky', 'title_en')}),
        ('Фотографии', {'fields': ('preview_image', 'main_image')}),
        ('Детальные иконки', {
            'fields': ('feature_aircondi', 'feature_power_windows', 'feature_sleeping_area', 
                      'feature_radio', 'feature_remote_control', 'feature_bluetooth', 
                      'feature_multifunction_steering'),
            'classes': ('collapse',),
        }),
        ('Детальные характеристики', {'fields': ('specs_accordion_html',)}),
        ('Служебная информация', {
            'fields': ('is_active', 'category', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related().prefetch_related('card_specs', 'mini_images')

    def mini_thumb(self, obj):
        return format_html('<img src="{}" width="60" style="border-radius:6px;">', obj.preview_image.url) if obj.preview_image else "—"
    mini_thumb.short_description = "Фото"

    def title_display(self, obj):
        return obj.title_ru or obj.title or '—'
    title_display.short_description = "Название"
    title_display.admin_order_field = 'title_ru'

    def category_badge(self, obj):
        colors = {'v': '#4CAF50', 'vr': '#2196F3', 'vh': '#FF9800'}
        labels = {'v': 'V Series', 'vr': 'VR Series', 'vh': 'VH Series'}
        return format_html(
            '<span style="background:{}; color:white; padding:5px 12px; border-radius:12px; font-weight:600; font-size:11px;">{}</span>',
            colors.get(obj.category, '#757575'), labels.get(obj.category, obj.category.upper())
        )
    category_badge.short_description = "Серия"

    def action_buttons(self, obj):
        frontend_url = f"http://localhost:5173/vehicle-details.html?id={obj.slug_ru or obj.slug}&lang=ru"
        return format_html(
            '<div style="display:flex; gap:8px;">'
            '<a href="{}"><img src="/static/media/icon-adminpanel/pencil.png" width="28"></a>'
            '<a href="{}" onclick="return confirm(\'Удалить {}?\')"><img src="/static/media/icon-adminpanel/recycle-bin.png" width="28"></a>'
            '<a href="{}" target="_blank"><img src="/static/media/icon-adminpanel/eyes.png" width="28"></a>'
            '</div>',
            f'/admin/kg/kgvehicle/{obj.id}/change/',
            f'/admin/kg/kgvehicle/{obj.id}/delete/',
            obj.title_ru or 'машину',
            frontend_url
        )
    action_buttons.short_description = "Действия"

    actions = ['activate_vehicles', 'deactivate_vehicles']

    def activate_vehicles(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано: {updated}')
    activate_vehicles.short_description = 'Активировать'

    def deactivate_vehicles(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ Деактивировано: {updated}')
    deactivate_vehicles.short_description = 'Деактивировать'

    def specs_accordion_html(self, obj):
        """Генерирует HTML аккордеона со встроенными стилями"""
        
        inline_css = """
        <style>
        .specs-accordion { 
            margin: 30px 0; 
            max-width: 100%;
        }
        
        .specs-accordion-item { 
            margin-bottom: 16px; 
            border: 2px solid #ddd; 
            border-radius: 12px; 
            overflow: visible;
            background: rgba(255, 255, 255, 0.95); 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .specs-accordion-header {
            width: 100%;
            padding: 18px 28px;
            background: linear-gradient(306deg, #000000, #002b9b, #1e57eb);
            color: white;
            border: none;
            text-align: left;
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 0.8px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            text-transform: uppercase;
            transition: all 0.3s ease;
            border-radius: 10px 10px 0 0;
        }
        
        .specs-accordion-header:hover {
            background: linear-gradient(306deg, #002b9b, #1e57eb, #225fff);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30, 87, 235, 0.3);
        }
        
        .specs-accordion-header.active {
            background: linear-gradient(64deg, #000000, #01164d, #225fff);
        }
        
        .specs-accordion-icon {
            font-size: 18px;
            font-weight: bold;
            transition: transform 0.3s ease;
        }
        
        .specs-accordion-header.active .specs-accordion-icon {
            transform: rotate(90deg);
        }
        
        .specs-accordion-content {
            max-height: 0;
            overflow: visible;
            transition: max-height 0.5s ease;
            background: #fafafa;
            opacity: 0;
        }
        
        .specs-accordion-content.active {
            max-height: 5000px;
            padding: 28px;
            opacity: 1;
            transition: max-height 0.5s ease, opacity 0.3s ease 0.2s;
        }
        
        .specs-accordion-content .form-row, 
        .translation-field { 
            display: grid; 
            grid-template-columns: 320px 1fr;
            gap: 20px;
            margin-bottom: 18px; 
            padding: 16px 22px;
            background: white; 
            border-radius: 10px; 
            border-left: 4px solid #002b9b;
            transition: all 0.2s ease;
        }
        
        .specs-accordion-content .form-row:hover,
        .translation-field:hover { 
            background: #f0f6ff; 
            border-left-color: #1e57eb;
            box-shadow: 0 3px 10px rgba(0,43,155,0.1);
        }
        
        .specs-accordion-content label { 
            font-weight: 600; 
            padding-top: 10px;
            font-size: 14px;
            color: #333;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .specs-accordion-content input, 
        .specs-accordion-content textarea { 
            width: 100%; 
            padding: 12px 16px;
            border: 2px solid #ddd; 
            border-radius: 8px;
            font-size: 14px;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
            transition: all 0.2s ease;
            min-height: 44px;
        }
        
        .specs-accordion-content input:focus, 
        .specs-accordion-content textarea:focus { 
            outline: none;
            border-color: #002b9b;
            box-shadow: 0 0 0 4px rgba(0, 43, 155, 0.1);
            background: #fff;
        }
        
        .specs-accordion-content textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .lang-badge { 
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 5px 12px; 
            border-radius: 8px; 
            font-size: 11px; 
            font-weight: 700; 
            color: white; 
            margin-right: 10px;
            min-width: 45px;
        }
        
        .lang-badge-ru { background: #002b9b; }
        .lang-badge-ky { background: #FF9800; }
        .lang-badge-en { background: #4CAF50; }
        
        /* Убираем надпись "Характеристики" */
        .field-specs_accordion_html > div > label {
            display: none !important;
        }
        </style>
        """
        
        inline_js = """
        <script>
        (function() {
            document.addEventListener('DOMContentLoaded', function() {
                const headers = document.querySelectorAll('.specs-accordion-header');
                
                headers.forEach(function(header) {
                    header.addEventListener('click', function() {
                        const content = this.nextElementSibling;
                        const isActive = this.classList.contains('active');
                        
                        document.querySelectorAll('.specs-accordion-header').forEach(function(h) {
                            h.classList.remove('active');
                        });
                        document.querySelectorAll('.specs-accordion-content').forEach(function(c) {
                            c.classList.remove('active');
                        });
                        
                        if (!isActive) {
                            this.classList.add('active');
                            content.classList.add('active');
                            
                            setTimeout(function() {
                                content.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                            }, 300);
                        }
                    });
                });
                
                if (headers[0]) {
                    headers[0].classList.add('active');
                    headers[0].nextElementSibling.classList.add('active');
                }
            });
        })();
        </script>
        """
        
        sections = [
            self._render_general_specs(obj),
            self._render_weight_specs(obj),
            self._render_body_specs(obj),
            self._render_engine_specs(obj),
            self._render_transmission_specs(obj),
            self._render_tires_specs(obj),
            self._render_cabin_specs(obj),
        ]
        
        return mark_safe(f'{inline_css}<div class="specs-accordion">{"".join(sections)}</div>{inline_js}')

    specs_accordion_html.short_description = "Характеристики"

    def _render_general_specs(self, obj):
        return f'''
        <div class="specs-accordion-item">
            <button type="button" class="specs-accordion-header">ОСНОВНЫЕ ХАРАКТЕРИСТИКИ <span>▶</span></button>
            <div class="specs-accordion-content">
                <div class="form-row"><label>Колесная формула</label><input type="text" name="wheel_formula" value="{obj.wheel_formula or ''}" maxlength="50"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Габаритные размеры, мм</label><input type="text" name="dimensions_ru" value="{obj.dimensions_ru or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Габаритные размеры, мм</label><input type="text" name="dimensions_ky" value="{obj.dimensions_ky or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Dimensions, mm</label><input type="text" name="dimensions_en" value="{obj.dimensions_en or ''}" maxlength="100"></div>
                <div class="form-row"><label>Колесная база, мм</label><input type="text" name="wheelbase" value="{obj.wheelbase or ''}" maxlength="50"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Вид топлива</label><input type="text" name="fuel_type_ru" value="{obj.fuel_type_ru or ''}" maxlength="50"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Вид топлива</label><input type="text" name="fuel_type_ky" value="{obj.fuel_type_ky or ''}" maxlength="50"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Fuel type</label><input type="text" name="fuel_type_en" value="{obj.fuel_type_en or ''}" maxlength="50"></div>
                <div class="form-row"><label>Объем топливного бака, л</label><input type="text" name="tank_volume" value="{obj.tank_volume or ''}" maxlength="50"></div>
            </div>
        </div>
        '''

    def _render_weight_specs(self, obj):
        return f'''
        <div class="specs-accordion-item">
            <button type="button" class="specs-accordion-header">ВЕСОВЫЕ ХАРАКТЕРИСТИКИ <span>▶</span></button>
            <div class="specs-accordion-content">
                <div class="form-row"><label>Снаряженная масса, кг</label><input type="text" name="curb_weight" value="{obj.curb_weight or ''}" maxlength="50"></div>
                <div class="form-row"><label>Грузоподъемность, кг</label><input type="text" name="payload" value="{obj.payload or ''}" maxlength="50"></div>
                <div class="form-row"><label>Полная масса, кг</label><input type="text" name="gross_weight" value="{obj.gross_weight or ''}" maxlength="50"></div>
            </div>
        </div>
        '''

    def _render_body_specs(self, obj):
        return f'''
        <div class="specs-accordion-item">
            <button type="button" class="specs-accordion-header">КУЗОВ <span>▶</span></button>
            <div class="specs-accordion-content">
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Тип</label><input type="text" name="body_type_ru" value="{obj.body_type_ru or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Тип</label><input type="text" name="body_type_ky" value="{obj.body_type_ky or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Type</label><input type="text" name="body_type_en" value="{obj.body_type_en or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Габариты, мм</label><input type="text" name="body_dimensions_ru" value="{obj.body_dimensions_ru or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Габариты, мм</label><input type="text" name="body_dimensions_ky" value="{obj.body_dimensions_ky or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Dimensions, mm</label><input type="text" name="body_dimensions_en" value="{obj.body_dimensions_en or ''}" maxlength="100"></div>
                <div class="form-row"><label>Объем надстройки, куб.м</label><input type="text" name="body_volume" value="{obj.body_volume or ''}" maxlength="50"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Материал надстройки</label><textarea name="body_material_ru" rows="3" maxlength="500">{obj.body_material_ru or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Материал надстройки</label><textarea name="body_material_ky" rows="3" maxlength="500">{obj.body_material_ky or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Body material</label><textarea name="body_material_en" rows="3" maxlength="500">{obj.body_material_en or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Вид загрузки</label><textarea name="loading_type_ru" rows="2" maxlength="500">{obj.loading_type_ru or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Вид загрузки</label><textarea name="loading_type_ky" rows="2" maxlength="500">{obj.loading_type_ky or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Loading type</label><textarea name="loading_type_en" rows="2" maxlength="500">{obj.loading_type_en or ''}</textarea></div>
            </div>
        </div>
        '''

    def _render_engine_specs(self, obj):
        return f'''
        <div class="specs-accordion-item">
            <button type="button" class="specs-accordion-header">ДВИГАТЕЛЬ <span>▶</span></button>
            <div class="specs-accordion-content">
                <div class="form-row"><label>Модель</label><input type="text" name="engine_model" value="{obj.engine_model or ''}" maxlength="100"></div>
                <div class="form-row"><label>Объем, л</label><input type="text" name="engine_volume" value="{obj.engine_volume or ''}" maxlength="50"></div>
                <div class="form-row"><label>Мощность, л.с.</label><input type="text" name="engine_power" value="{obj.engine_power or ''}" maxlength="50"></div>
            </div>
        </div>
        '''

    def _render_transmission_specs(self, obj):
        return f'''
        <div class="specs-accordion-item">
            <button type="button" class="specs-accordion-header">ТРАНСМИССИЯ <span>▶</span></button>
            <div class="specs-accordion-content">
                <div class="form-row"><label>Модель</label><input type="text" name="transmission_model" value="{obj.transmission_model or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Тип</label><input type="text" name="transmission_type_ru" value="{obj.transmission_type_ru or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Тип</label><input type="text" name="transmission_type_ky" value="{obj.transmission_type_ky or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Type</label><input type="text" name="transmission_type_en" value="{obj.transmission_type_en or ''}" maxlength="100"></div>
                <div class="form-row"><label>Число передач</label><input type="text" name="gears" value="{obj.gears or ''}" maxlength="50"></div>
            </div>
        </div>
        '''

    def _render_tires_specs(self, obj):
        return f'''
        <div class="specs-accordion-item">
            <button type="button" class="specs-accordion-header">ШИНЫ И ТОРМОЗНАЯ СИСТЕМА <span>▶</span></button>
            <div class="specs-accordion-content">
                <div class="form-row"><label>Шины</label><input type="text" name="tire_type" value="{obj.tire_type or ''}" maxlength="100"></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Подвеска</label><textarea name="suspension_ru" rows="2" maxlength="500">{obj.suspension_ru or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Подвеска</label><textarea name="suspension_ky" rows="2" maxlength="500">{obj.suspension_ky or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Suspension</label><textarea name="suspension_en" rows="2" maxlength="500">{obj.suspension_en or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Тормоза</label><textarea name="brakes_ru" rows="2" maxlength="500">{obj.brakes_ru or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Тормоза</label><textarea name="brakes_ky" rows="2" maxlength="500">{obj.brakes_ky or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Brakes</label><textarea name="brakes_en" rows="2" maxlength="500">{obj.brakes_en or ''}</textarea></div>
            </div>
        </div>
        '''

    def _render_cabin_specs(self, obj):
        return f'''
        <div class="specs-accordion-item">
            <button type="button" class="specs-accordion-header">КАБИНА <span>▶</span></button>
            <div class="specs-accordion-content">
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Модель кабины</label><textarea name="cabin_category_ru" rows="2" maxlength="500">{obj.cabin_category_ru or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Модель кабины</label><textarea name="cabin_category_ky" rows="2" maxlength="500">{obj.cabin_category_ky or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Cabin model</label><textarea name="cabin_category_en" rows="2" maxlength="500">{obj.cabin_category_en or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ru">RU</span> Комплектация</label><textarea name="cabin_equipment_ru" rows="3" maxlength="500">{obj.cabin_equipment_ru or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-ky">KY</span> Комплектация</label><textarea name="cabin_equipment_ky" rows="3" maxlength="500">{obj.cabin_equipment_ky or ''}</textarea></div>
                <div class="translation-field"><label><span class="lang-badge lang-badge-en">EN</span> Equipment</label><textarea name="cabin_equipment_en" rows="3" maxlength="500">{obj.cabin_equipment_en or ''}</textarea></div>
            </div>
        </div>
        '''

# ============================================
# ADMIN: HERO-СЛАЙДЫ
# ============================================

@admin.register(KGHeroSlide)
class KGHeroSlideAdmin(admin.ModelAdmin):
    list_display = ('order', 'vehicle_display', 'is_active', 'created_at')
    list_display_links = ('vehicle_display',)
    list_editable = ('is_active', 'order')
    list_filter = ('is_active', 'created_at')
    search_fields = ('vehicle__title_ru', 'description_ru')
    readonly_fields = ('created_at', 'vehicle_preview')
    list_select_related = ('vehicle',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('vehicle', 'vehicle_preview', 'order', 'is_active')
        }),
        ('Описание (Русский)', {
            'fields': ('description_ru',),
        }),
        ('Описание (Кыргызский)', {
            'fields': ('description_ky',),
        }),
        ('Описание (Английский)', {
            'fields': ('description_en',),
        }),
    )

    def vehicle_display(self, obj):
        return obj.vehicle.title_ru if obj.vehicle else '—'
    vehicle_display.short_description = "Машина"
    vehicle_display.admin_order_field = 'vehicle__title_ru'

    def vehicle_preview(self, obj):
        if not obj.vehicle:
            return "—"
        img = obj.vehicle.main_image or obj.vehicle.preview_image
        return format_html('<img src="{}" width="200" style="border-radius:8px;">', img.url) if img else "—"
    vehicle_preview.short_description = "Превью"


# ============================================
# ADMIN: ЗАЯВКИ
# ============================================

@admin.register(KGFeedback)
class KGFeedbackAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'region', 'vehicle_display', 'priority', 'status', 'manager', 'created_at']
    list_editable = ['priority', 'status', 'manager']
    list_filter = ['status', 'priority', 'region', 'created_at']
    search_fields = ['name', 'phone', 'vehicle__title_ru']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    actions = ['export_to_excel', 'mark_as_done']
    list_select_related = ('vehicle', 'manager')
        
        
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('name', 'phone', 'region', 'vehicle', 'message', 'created_at')
        }),
        ('Управление', {
            'fields': ('status', 'priority', 'manager', 'admin_comment')
        }),
    )

    def vehicle_display(self, obj):
        return obj.vehicle.title_ru if obj.vehicle else '—'
    vehicle_display.short_description = "Машина"
    vehicle_display.admin_order_field = 'vehicle__title_ru'

    def mark_as_done(self, request, queryset):
        updated = queryset.update(status='done')
        self.message_user(request, f'✅ Обработано заявок: {updated}')
    mark_as_done.short_description = 'Отметить как обработанные'

    def export_to_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заявки FAW KG"

        # Заголовки
        headers = ['№', 'ФИО', 'Телефон', 'Регион', 'Машина', 'Статус', 'Приоритет', 'Менеджер', 'Дата']
        ws.append(headers)

        # Стилизация
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Данные
        for idx, feedback in enumerate(queryset.select_related('vehicle', 'manager'), start=1):
            ws.append([
                idx,
                feedback.name,
                feedback.phone,
                feedback.get_region_display(),
                feedback.vehicle.title_ru if feedback.vehicle else '-',
                feedback.get_status_display(),
                feedback.get_priority_display(),
                feedback.manager.username if feedback.manager else '-',
                feedback.created_at.strftime('%d.%m.%Y %H:%M')
            ])

        # Автоширина
        for column in ws.columns:
            max_length = max(len(str(cell.value)) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)

        # Отправка
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="faw_kg_leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response

    export_to_excel.short_description = 'Экспорт в Excel'


# ============================================
# ADMIN: ШАБЛОНЫ ИКОНОК
# ============================================

@admin.register(IconTemplate)
class IconTemplateAdmin(admin.ModelAdmin):
    list_display = ('icon_preview', 'name', 'order', 'created_display')
    list_editable = ('order',)
    fields = ('name', 'icon', 'icon_preview', 'order')
    readonly_fields = ('icon_preview',)
    list_per_page = 50
    
    def icon_preview(self, obj):
        return format_html('<img src="{}" width="60" style="border-radius:8px;">', obj.icon.url) if obj.icon else "—"
    icon_preview.short_description = "Превью"
    
    def created_display(self, obj):
        return "—"
    created_display.short_description = "Создано"