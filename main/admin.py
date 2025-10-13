from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse, HttpResponseRedirect
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from .models import (
    News, NewsBlock, ContactForm, 
    KGVehicle, KGVehicleImage,
    KGFeedback, VehicleCardSpec, KGHeroSlide
)
import openpyxl
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


# Основные админки
@admin.register(KGVehicle)
class KGVehicleAdmin(admin.ModelAdmin):
    list_display = ('preview_thumb', 'title_display', 'category_badge', 'is_active', 'created_at', 'action_buttons')
    list_editable = ('is_active',)
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'title_ru', 'title_ky', 'title_en', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('preview_thumb', 'main_thumb', 'created_at', 'updated_at', 'category')
    inlines = [VehicleCardSpecInline, KGVehicleImageInline]
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
        }),
        ('Изображения', {
            'fields': ('preview_image', 'preview_thumb', 'main_image', 'main_thumb')
        }),
        ('Характеристики', {
            'fields': ('specs_ru', 'specs_ky', 'specs_en'),
            'classes': ('collapse',),
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'is_active' in request.GET:
            if request.GET['is_active'] == '1':
                qs = qs.filter(is_active=True)
            elif request.GET['is_active'] == '0':
                qs = qs.filter(is_active=False)
        return qs
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Каталог машин FAW.KG'
        
        # Кнопки фильтрации
        extra_context['custom_filters'] = format_html('''
            <div style="margin: 15px 0; display: flex; gap: 10px;">
                <a href="?" style="background: {}; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    Все ({})
                </a>
                <a href="?is_active=1" style="background: {}; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    ✓ Активные ({})
                </a>
                <a href="?is_active=0" style="background: {}; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    ✗ Неактивные ({})
                </a>
            </div>
        ''',
            '#9E9E9E' if request.GET.get('is_active') else '#607D8B',
            KGVehicle.objects.count(),
            '#4CAF50' if request.GET.get('is_active') == '1' else '#9E9E9E',
            KGVehicle.objects.filter(is_active=True).count(),
            '#F44336' if request.GET.get('is_active') == '0' else '#9E9E9E',
            KGVehicle.objects.filter(is_active=False).count()
        )
        
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
        colors = {'v': '#4CAF50', 'vr': '#2196F3', 'vh': '#FF9800'}
        labels = {'v': 'V Series', 'vr': 'VR Series', 'vh': 'VH Series'}
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 12px; font-weight: 600; font-size: 11px;">{}</span>',
            colors.get(obj.category, '#757575'), labels.get(obj.category, obj.category.upper())
        )
    category_badge.short_description = "Серия"
    
    def is_active_badge(self, obj):
        return format_html(
            '<span style="color: {}; font-size: 18px;">{}</span>',
            '#4CAF50' if obj.is_active else '#F44336',
            '✅' if obj.is_active else '❌'
        )
    is_active_badge.short_description = "Статус"
    
    def action_buttons(self, obj):
        return format_html('''
            <div style="display: flex; gap: 8px;">
                <a href="{}" title="Посмотреть" style="font-size: 20px;">👁</a>
                <a href="{}" title="Редактировать" style="font-size: 20px;">✏️</a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить?')" style="font-size: 20px;">🗑</a>
            </div>
        ''',
            f'/admin/main/kgvehicle/{obj.id}/change/',
            f'/admin/main/kgvehicle/{obj.id}/change/',
            f'/admin/main/kgvehicle/{obj.id}/delete/'
        )
    action_buttons.short_description = "Действия"
    
    def activate_vehicles(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано: {updated}')
    activate_vehicles.short_description = '✅ Активировать'
    
    def deactivate_vehicles(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ Деактивировано: {updated}')
    deactivate_vehicles.short_description = '❌ Деактивировать'


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
                obj.vehicle.preview_image.url, obj.vehicle.title
            )
        return "—"
    vehicle_preview.short_description = "Превью"


@admin.register(KGFeedback)
class KGFeedbackAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'region', 'vehicle', 'priority_editable', 'status_editable', 'manager_editable', 'created_at']
    list_filter = ['status', 'priority', 'region', 'created_at', 'vehicle', 'manager']
    search_fields = ['name', 'phone', 'message', 'admin_comment']
    readonly_fields = ['created_at']
    autocomplete_fields = ['vehicle', 'manager']
    date_hierarchy = 'created_at'
    actions = ['export_to_excel']
    
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('name', 'phone', 'region', 'vehicle', 'message', 'created_at')
        }),
        ('Управление', {
            'fields': ('status', 'priority', 'manager', 'admin_comment'),
            'classes': ('wide',)
        }),
    )
    
    class Media:
        css = {'all': ('admin/css/custom_feedback.css',)}
        js = ('admin/js/feedback_inline_edit.js',)
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Заявки FAW.KG'
        
        # Кнопки фильтрации статусов
        extra_context['status_filters'] = format_html('''
            <div style="margin: 20px 0; display: flex; gap: 12px; align-items: center;">
                <a href="?" style="background: {}; color: white; padding: 12px 24px; border-radius: 25px; text-decoration: none; font-weight: 700; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: all 0.3s;">
                    Все ({})
                </a>
                <a href="?status=new" style="background: {}; color: white; padding: 12px 24px; border-radius: 25px; text-decoration: none; font-weight: 700; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    🟢 Новые ({})
                </a>
                <a href="?status=in_process" style="background: {}; color: white; padding: 12px 24px; border-radius: 25px; text-decoration: none; font-weight: 700; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    🟡 В процессе ({})
                </a>
                <a href="?status=done" style="background: {}; color: white; padding: 12px 24px; border-radius: 25px; text-decoration: none; font-weight: 700; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    ✅ Обработано ({})
                </a>
            </div>
        ''',
            'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' if not request.GET.get('status') else '#9E9E9E',
            KGFeedback.objects.count(),
            '#4CAF50' if request.GET.get('status') == 'new' else '#9E9E9E',
            KGFeedback.objects.filter(status='new').count(),
            '#FF9800' if request.GET.get('status') == 'in_process' else '#9E9E9E',
            KGFeedback.objects.filter(status='in_process').count(),
            '#2196F3' if request.GET.get('status') == 'done' else '#9E9E9E',
            KGFeedback.objects.filter(status='done').count()
        )
        
        return super().changelist_view(request, extra_context)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'status' in request.GET:
            qs = qs.filter(status=request.GET['status'])
        return qs
    
    def priority_editable(self, obj):
        from django.contrib.auth.models import User
        return format_html('''
            <select onchange="updateField(this, 'priority', {})" style="background: {}; color: white; padding: 8px 15px; border-radius: 20px; border: none; font-weight: 600; cursor: pointer; font-size: 12px;">
                <option value="high" {}>🔥 Высокий</option>
                <option value="medium" {}>🟡 Средний</option>
                <option value="low" {}>❄️ Низкий</option>
            </select>
        ''',
            obj.id,
            '#F44336' if obj.priority == 'high' else '#FF9800' if obj.priority == 'medium' else '#4CAF50',
            'selected' if obj.priority == 'high' else '',
            'selected' if obj.priority == 'medium' else '',
            'selected' if obj.priority == 'low' else ''
        )
    priority_editable.short_description = "Приоритет"
    
    def status_editable(self, obj):
        return format_html('''
            <select onchange="updateField(this, 'status', {})" style="background: {}; color: white; padding: 8px 15px; border-radius: 20px; border: none; font-weight: 600; cursor: pointer; font-size: 12px;">
                <option value="new" {}>🟢 Новая</option>
                <option value="in_process" {}>🟡 В процессе</option>
                <option value="done" {}>✅ Обработана</option>
            </select>
        ''',
            obj.id,
            '#4CAF50' if obj.status == 'new' else '#FF9800' if obj.status == 'in_process' else '#2196F3',
            'selected' if obj.status == 'new' else '',
            'selected' if obj.status == 'in_process' else '',
            'selected' if obj.status == 'done' else ''
        )
    status_editable.short_description = "Статус"
    
    def manager_editable(self, obj):
        from django.contrib.auth.models import User
        managers = User.objects.filter(is_staff=True)
        options = '<option value="">-</option>'
        for m in managers:
            selected = 'selected' if obj.manager and obj.manager.id == m.id else ''
            options += f'<option value="{m.id}" {selected}>{m.username}</option>'
        
        return format_html('''
            <select onchange="updateField(this, 'manager', {})" style="padding: 8px 15px; border-radius: 20px; border: 2px solid #2196F3; font-weight: 600; cursor: pointer; font-size: 12px;">
                {}
            </select>
        ''', obj.id, options)
    manager_editable.short_description = "Ответственный"
    
    def export_to_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заявки FAW KG"
        
        headers = ['№', 'ФИО', 'Телефон', 'Регион', 'Машина', 'Статус', 'Приоритет', 'Менеджер', 'Дата']
        ws.append(headers)
        
        from openpyxl.styles import Font, PatternFill, Alignment
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for idx, feedback in enumerate(queryset, start=1):
            ws.append([
                idx, feedback.name, feedback.phone,
                feedback.get_region_display(),
                feedback.vehicle.title if feedback.vehicle else '-',
                feedback.get_status_display(),
                feedback.get_priority_display(),
                feedback.manager.username if feedback.manager else '-',
                feedback.created_at.strftime('%d.%m.%Y %H:%M')
            ])
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="faw_kg_leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response
    
    export_to_excel.short_description = '📥 Экспорт в Excel'