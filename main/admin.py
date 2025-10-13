from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from .models import (
    News, NewsBlock, ContactForm, 
    KGVehicle, KGVehicleImage, KGVehicleFeature, FeatureIcon, 
    KGFeedback, VehicleCardSpec, KGHeroSlide
)
import openpyxl
from django.http import HttpResponse
from datetime import datetime

# Кастомизация админки
admin.site.site_header = "VUM Admin Panel"
admin.site.site_title = "VUM"
admin.site.index_title = "Управление сайтами FAW"


# ============ FAW.UZ МОДЕЛИ ============

class NewsBlockInline(TranslationTabularInline):
    model = NewsBlock
    extra = 1
    fields = ('block_type', 'text', 'image', 'youtube_url', 'video_file', 'order', 'image_tag')
    readonly_fields = ('image_tag',)

    class Media:
        js = ('main/admin.js',)
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

    def image_tag(self, obj):
        if obj.image and obj.image.name:
            return format_html(
                '<img src="{}" width="100" style="border-radius:8px;">',
                obj.image.url
            )
        return "—"
    image_tag.short_description = "Превью блока"


@admin.register(News)
class NewsAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'author', 'preview_image_tag', 'created_at')
    readonly_fields = ('preview_image_tag', 'author_photo_tag')
    search_fields = ('title', 'author__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    inlines = [NewsBlockInline]
    
    def preview_image_tag(self, obj):
        if obj.preview_image and obj.preview_image.name:
            return format_html(
                '<img src="{}" width="100" style="border-radius:8px;">',
                obj.preview_image.url
            )
        return "—"
    preview_image_tag.short_description = "Превью"

    def author_photo_tag(self, obj):
        if obj.author_photo and obj.author_photo.name:
            return format_html(
                '<img src="{}" width="50" style="border-radius:50%;">',
                obj.author_photo.url
            )
        return "—"
    author_photo_tag.short_description = "Фото автора"


@admin.register(ContactForm)
class ContactFormAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'region', 'created_at', 'is_processed']
    list_filter = ['is_processed', 'region', 'created_at']
    search_fields = ['name', 'phone', 'message', 'admin_comment']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Информация о заявке', {
            'fields': ('name', 'phone', 'region', 'message', 'created_at')
        }),
        ('Обработка', {
            'fields': ('is_processed', 'admin_comment'),
            'classes': ('wide',)
        }),
    )
    
    actions = ['mark_as_processed']
    
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(is_processed=True)
        self.message_user(request, f'{updated} - помечены как просмотренные.')
    mark_as_processed.short_description = 'Пометить как просмотренные'


# ============ FAW.KG МОДЕЛИ ============

# Inline классы
class VehicleCardSpecInline(admin.TabularInline):
    model = VehicleCardSpec
    extra = 1
    fields = ('icon', 'icon_preview', 'value_ru', 'value_ky', 'value_en', 'order')
    readonly_fields = ('icon_preview',)
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="40" style="border-radius:4px;">', obj.icon.url)
        return "—"
    icon_preview.short_description = "Превью"


class KGVehicleImageInline(admin.TabularInline):
    model = KGVehicleImage
    extra = 1
    fields = ('image', 'alt', 'order', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" style="border-radius:4px;">', obj.image.url)
        return "—"
    image_preview.short_description = "Превью"


class KGVehicleFeatureInline(admin.TabularInline):
    model = KGVehicleFeature
    extra = 1
    autocomplete_fields = ['feature']


# Основные админки
@admin.register(KGVehicle)
class KGVehicleAdmin(admin.ModelAdmin):
    list_display = ('preview_thumb', 'title_display', 'category_badge', 'is_active_badge', 'created_at', 'action_buttons')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('title', 'title_ru', 'title_ky', 'title_en', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('preview_thumb', 'main_thumb', 'created_at', 'updated_at', 'category')
    inlines = [VehicleCardSpecInline, KGVehicleImageInline, KGVehicleFeatureInline]
    list_per_page = 20
    actions = ['activate_vehicles', 'deactivate_vehicles']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('is_active', 'category'),
            'description': 'Категория определяется автоматически по названию (VR, VH или V)'
        }),
        ('Переводы названия', {
            'fields': (
                ('title', 'slug'),
                ('title_ru', 'slug_ru'),
                ('title_ky', 'slug_ky'),
                ('title_en', 'slug_en'),
            ),
            'classes': ('wide',),
            'description': '🇷🇺 Русский | 🇰🇬 Кыргызский | 🇬🇧 Английский'
        }),
        ('Изображения', {
            'fields': ('preview_image', 'preview_thumb', 'main_image', 'main_thumb')
        }),
        ('Характеристики', {
            'fields': ('specs_ru', 'specs_ky', 'specs_en'),
            'classes': ('collapse',),
            'description': '''
                <div style="background: #e8f4f8; padding: 15px; border-left: 4px solid #2196F3; margin-bottom: 10px;">
                    <strong>📝 Как заполнять JSON:</strong><br>
                    Скопируйте этот шаблон и замените значения:
                </div>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 13px;">
    {
        "wheelFormula": "4x2",
        "dimensions": "7330×2350×2560",
        "wheelbase": "3900",
        "fuelType": "Дизель",
        "tankVolume": "100",
        "curbWeight": "4380",
        "payload": "6920",
        "grossWeight": "11300",
        "engineModel": "YUCHAI YC4D130-33",
        "engineVolume": "4.2",
        "enginePower": "130",
        "bodyType": "бортовой"
    }</pre>
                '''
        }),
        ('🕐 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Каталог машин FAW.KG'
        return super().changelist_view(request, extra_context)
    
    def title_display(self, obj):
        return obj.title_ru or obj.title or '—'
    title_display.short_description = "Название"
    
    def preview_thumb(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" width="80" style="border-radius:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">', obj.preview_image.url)
        return "—"
    preview_thumb.short_description = "Фото"
    
    def main_thumb(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="100" style="border-radius:8px;">', obj.main_image.url)
        return "—"
    main_thumb.short_description = "Главное фото"
    
    def category_badge(self, obj):
        colors = {
            'v': '#4CAF50',
            'vr': '#2196F3',
            'vh': '#FF9800'
        }
        labels = {
            'v': 'V Series',
            'vr': 'VR Series',
            'vh': 'VH Series'
        }
        color = colors.get(obj.category, '#757575')
        label = labels.get(obj.category, obj.category.upper())
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 12px; font-weight: 600; font-size: 11px; display: inline-block;">{}</span>',
            color, label
        )
    category_badge.short_description = "Серия"
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #4CAF50; font-size: 18px;" title="Активно">✅</span>'
            )
        return format_html(
            '<span style="color: #F44336; font-size: 18px;" title="Неактивно">❌</span>'
        )
    is_active_badge.short_description = "Статус"
    
    def activate_vehicles(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано машин: {updated}')
    activate_vehicles.short_description = '✅ Активировать выбранные'
    
    def deactivate_vehicles(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ Деактивировано машин: {updated}')
    deactivate_vehicles.short_description = '❌ Деактивировать выбранные'
    def action_buttons(self, obj):
        return format_html(
            '''
            <div style="display: flex; gap: 8px;">
                <a href="{}" title="Посмотреть" style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: #white; color: white; border-radius: 50%; text-decoration: none; font-size: 20px;">👁</a>
                <a href="{}" title="Редактировать" style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: #white; color: white; border-radius: 50%; text-decoration: none; font-size: 20px;">✏️</a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить эту машину?')" style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: #white; color: white; border-radius: 50%; text-decoration: none; font-size: 20px;">🗑</a>
            </div>
            ''',
            f'/admin/main/kgvehicle/{obj.id}/change/',
            f'/admin/main/kgvehicle/{obj.id}/change/',
            f'/admin/main/kgvehicle/{obj.id}/delete/'
        )
    action_buttons.short_description = "Действия"

@admin.register(FeatureIcon)
class FeatureIconAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_preview')
    search_fields = ('name',)
    
    def icon_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40">', obj.image.url)
        return "—"
    icon_preview.short_description = "Иконка"


@admin.register(KGHeroSlide)
class KGHeroSlideAdmin(admin.ModelAdmin):
    list_display = ('order', 'vehicle', 'vehicle_preview', 'is_active', 'created_at')
    list_display_links = ('order', 'vehicle')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'created_at')
    autocomplete_fields = ['vehicle']
    readonly_fields = ('created_at', 'vehicle_preview')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('vehicle', 'vehicle_preview', 'order', 'is_active')
        }),
        ('Дополнительно', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def vehicle_preview(self, obj):
        if obj.vehicle and obj.vehicle.preview_image:
            return format_html(
                '<img src="{}" width="150" style="border-radius:8px;"><br><b>{}</b>',
                obj.vehicle.preview_image.url,
                obj.vehicle.title
            )
        return "—"
    vehicle_preview.short_description = "Превью машины"


@admin.register(KGFeedback)
class KGFeedbackAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'region', 'vehicle', 'created_at', 'is_processed_badge']
    list_filter = ['is_processed', 'region', 'created_at', 'vehicle']
    search_fields = ['name', 'phone', 'message', 'admin_comment']
    readonly_fields = ['created_at']
    autocomplete_fields = ['vehicle']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('name', 'phone', 'region', 'vehicle', 'message', 'created_at')
        }),
        ('Обработка', {
            'fields': ('is_processed', 'admin_comment'),
            'classes': ('wide',)
        }),
    )
    
    actions = ['mark_as_processed', 'export_to_excel']
    
    def is_processed_badge(self, obj):
        if obj.is_processed:
            color = 'green'
            text = '✓ Обработано'
        else:
            color = 'red'
            text = '✗ Новая'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, text
        )
    is_processed_badge.short_description = 'Статус'
    
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(is_processed=True)
        self.message_user(request, f'{updated} заявок отмечено как обработанные.')
    mark_as_processed.short_description = 'Отметить как обработанные'
    
    def export_to_excel(self, request, queryset):
        """Экспорт выбранных заявок в Excel"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заявки FAW KG"
        
        # Заголовки
        headers = ['№', 'ФИО', 'Телефон', 'Регион', 'Машина', 'Сообщение', 'Дата', 'Обработано']
        ws.append(headers)
        
        # Стилизация заголовков
        from openpyxl.styles import Font, PatternFill, Alignment
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Данные
        for idx, feedback in enumerate(queryset, start=1):
            ws.append([
                idx,
                feedback.name,
                feedback.phone,
                feedback.get_region_display(),
                feedback.vehicle.title if feedback.vehicle else '-',
                feedback.message or '-',
                feedback.created_at.strftime('%d.%m.%Y %H:%M'),
                'Да' if feedback.is_processed else 'Нет'
            ])
        
        # Автоширина колонок
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Отправка файла
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="faw_kg_leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        
        return response
    
    export_to_excel.short_description = 'Экспорт в Excel'