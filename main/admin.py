from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from .models import News, NewsBlock, ContactForm, KGVehicle, KGVehicleImage, KGVehicleFeature, FeatureIcon, KGFeedback
import openpyxl
from django.http import HttpResponse
from datetime import datetime


class NewsBlockInline(TranslationTabularInline):
    model = NewsBlock
    extra = 1
    # Не указывайте явно поля переводов - modeltranslation добавит их автоматически
    fields = ('block_type', 'text', 'image', 'youtube_url', 'video_file', 'order', 'image_tag')
    readonly_fields = ('image_tag',)

    class Media:
        js = ('main/admin.js',)
        # Добавляем CSS для вкладок
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
class NewsAdmin(TabbedTranslationAdmin):  # Вкладки для переводов
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

# @admin.register(NewsBlock)
# class NewsBlockAdmin(admin.ModelAdmin):
#     list_display = ('news', 'order', 'block_type', 'short_text', 'image_tag')
#     ordering = ('news', 'order')
#     raw_id_fields = ('news',)  # безопасно для ForeignKey при большом количестве новостей

#     # readonly_fields только при редактировании, чтобы не ломать курсор
#     def get_readonly_fields(self, request, obj=None):
#         if obj:  # редактирование
#             return ('image_tag',)
#         return ()

#     def image_tag(self, obj):
#         if obj.image and obj.image.name:
#             return format_html(
#                 '<img src="{}" width="100" style="border-radius:8px;">',
#                 obj.image.url
#             )
#         return "—"
#     image_tag.short_description = "Изображение"

#     def short_text(self, obj):
#         if obj.text:
#             return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
#         return "—"
#     short_text.short_description = "Текст"

# В конце файла main/admin.py добавьте:




# ============ НОВЫЙ КОД ДЛЯ FAW.KG ============

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


@admin.register(KGVehicle)
class KGVehicleAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'preview_thumb', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'title_ru', 'title_ky', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('preview_thumb', 'main_thumb', 'created_at', 'updated_at')
    inlines = [KGVehicleImageInline, KGVehicleFeatureInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('is_active',)
        }),
        ('Название и URL', {
            'fields': (
                ('title', 'slug'),
                ('title_ru', 'slug_ru'),
                ('title_ky', 'slug_ky'),
            ),
            'description': 'Заполните название и URL для русского и киргизского языков'
        }),
        ('Изображения', {
            'fields': ('preview_image', 'preview_thumb', 'main_image', 'main_thumb')
        }),
        ('Характеристики', {
            'fields': ('specs', 'specs_ru', 'specs_ky'),
            'classes': ('collapse',),
            'description': 'JSON формат: {"двигатель": "2.0L", "мощность": "150 л.с."}'
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        css = {
            'all': ('admin/css/kg_vehicle_admin.css',)  # можно добавить свои стили
        }
    
    def preview_thumb(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" width="100" style="border-radius:8px;">', obj.preview_image.url)
        return "—"
    preview_thumb.short_description = "Превью для каталога"
    
    def main_thumb(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="100" style="border-radius:8px;">', obj.main_image.url)
        return "—"
    main_thumb.short_description = "Главное фото"


@admin.register(FeatureIcon)
class FeatureIconAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_preview')
    search_fields = ('name',)
    
    def icon_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40">', obj.image.url)
        return "—"
    icon_preview.short_description = "Иконка"


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