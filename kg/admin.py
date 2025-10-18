from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from .models import KGVehicle, KGVehicleImage, VehicleCardSpec, KGFeedback, KGHeroSlide, IconTemplate
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime


# ============================================
# INLINE: ХАРАКТЕРИСТИКИ ДЛЯ КАТАЛОГА
# ============================================

class VehicleCardSpecInline(admin.TabularInline):
    model = VehicleCardSpec
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
    # Список
    list_display = ('mini_thumb', 'title_display', 'category_badge', 'is_active', 'created_at', 'action_buttons')
    list_editable = ('is_active',)
    list_filter = ('category', 'is_active', 'created_at')
    list_select_related = True
    search_fields = ('title_ru', 'title_ky', 'title_en', 'slug')
    readonly_fields = ('created_at', 'updated_at', 'category')
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    # Inline'ы
    inlines = [VehicleCardSpecInline, KGVehicleImageInline]
    
    class Media:
        css = {
        'all': ('kg/admin/js/vehicle_admin.css',)  # ← ДОБАВИЛ kg/
    }

    # Структура формы
    fieldsets = (
        # 1. Название техники
        ('Название техники', {
            'fields': ('title_ru', 'title_ky', 'title_en'),
        }),
        
        # 2. Фотографии
        ('Фотографии', {
            'fields': ('preview_image', 'main_image'),
        }),
        
        # 3. Характеристики для каталога - inline (через template)
        
        # 4. Детальные иконки
        ('Детальные иконки', {
            'fields': (
                ('feature_aircondi', 'feature_power_windows', 'feature_sleeping_area'),
                ('feature_radio', 'feature_remote_control', 'feature_bluetooth'),
                ('feature_multifunction_steering',),
            ),
            'description': 'Отметьте иконки для страницы детализации',
            'classes': ('collapse',),
        }),
        
        # 5. Детальные характеристики
        ('Детальные характеристики', {
            'fields': (
                'wheel_formula',
                ('dimensions_ru', 'dimensions_ky', 'dimensions_en'),
                'wheelbase',
                ('fuel_type_ru', 'fuel_type_ky', 'fuel_type_en'),
                'tank_volume',
                'curb_weight',
                'payload',
                'gross_weight',
                ('body_type_ru', 'body_type_ky', 'body_type_en'),
                ('body_dimensions_ru', 'body_dimensions_ky', 'body_dimensions_en'),
                'body_volume',
                ('body_material_ru', 'body_material_ky', 'body_material_en'),
                ('loading_type_ru', 'loading_type_ky', 'loading_type_en'),
                'engine_model',
                'engine_volume',
                'engine_power',
                'transmission_model',
                ('transmission_type_ru', 'transmission_type_ky', 'transmission_type_en'),
                'gears',
                'tire_type',
                ('suspension_ru', 'suspension_ky', 'suspension_en'),
                ('brakes_ru', 'brakes_ky', 'brakes_en'),
                ('cabin_category_ru', 'cabin_category_ky', 'cabin_category_en'),
                ('cabin_equipment_ru', 'cabin_equipment_ky', 'cabin_equipment_en'),
            ),
            'classes': ('collapse',),
        }),
        
        # 6. Дополнительные фото - inline (через template)
        
        # 7. Служебная информация
        ('Служебная информация', {
            'fields': ('is_active', 'category', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    # === ОПТИМИЗАЦИЯ ЗАПРОСОВ ===
    def get_queryset(self, request):
        return super().get_queryset(request).select_related().prefetch_related('card_specs', 'mini_images')

    # === МЕТОДЫ ОТОБРАЖЕНИЯ ===
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
            colors.get(obj.category, '#757575'), 
            labels.get(obj.category, obj.category.upper())
        )
    category_badge.short_description = "Серия"
    category_badge.admin_order_field = 'category'

    def action_buttons(self, obj):
        frontend_url = f"http://localhost:5173/vehicle-details.html?id={obj.slug_ru or obj.slug}&lang=ru"
        
        return format_html(
            '<div style="display:flex; gap:8px;">'
            '<a href="{edit}" title="Редактировать" style="display:inline-block;">'
            '<img src="/static/media/icon-adminpanel/pencil.png" width="28" height="28"></a>'
            '<a href="{delete}" title="Удалить" onclick="return confirm(\'Удалить {title}?\')" style="display:inline-block;">'
            '<img src="/static/media/icon-adminpanel/recycle-bin.png" width="28" height="28"></a>'
            '<a href="{view}" target="_blank" title="Посмотреть на сайте" style="display:inline-block;">'
            '<img src="/static/media/icon-adminpanel/eyes.png" width="28" height="28"></a>'
            '</div>',
            edit=f'/admin/kg/kgvehicle/{obj.id}/change/',
            delete=f'/admin/kg/kgvehicle/{obj.id}/delete/',
            view=frontend_url,
            title=obj.title_ru or 'машину'
        )
    action_buttons.short_description = "Действия"

    # === ДЕЙСТВИЯ ===
    actions = ['activate_vehicles', 'deactivate_vehicles']

    def activate_vehicles(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано машин: {updated}')
    activate_vehicles.short_description = 'Активировать выбранные'

    def deactivate_vehicles(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ Деактивировано машин: {updated}')
    deactivate_vehicles.short_description = 'Деактивировать выбранные'


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