from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import KGVehicle, KGVehicleImage, VehicleCardSpec, KGFeedback, KGHeroSlide
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime


# ============ ТОЛЬКО FAW.KG ============

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
            'description': 'Категория определяется автоматически'
        }),
        ('Переводы названия', {
            'fields': (
                ('title', 'slug'),
                ('title_ru', 'slug_ru'),
                ('title_ky', 'slug_ky'),
                ('title_en', 'slug_en'),
            )
        }),
        ('Изображения', {
            'fields': ('preview_image', 'preview_thumb', 'main_image', 'main_thumb')
        }),
        ('Характеристики', {
            'fields': ('specs_ru', 'specs_ky', 'specs_en'),
            'classes': ('collapse',)
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'is_active' in request.GET:
            qs = qs.filter(is_active=request.GET['is_active'] == '1')
        return qs

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Каталог машин FAW.KG'

        extra_context['custom_filters'] = format_html('''
            <div style="margin: 15px 0; display: flex; gap: 10px;">
                <a href="?" style="background: {}; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                    Все ({})
                </a>
                <a href="?is_active=1" style="background: {}; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                    ✓ Активные ({})
                </a>
                <a href="?is_active=0" style="background: {}; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                    ✗ Неактивные ({})
                </a>
            </div>
        ''',
            '#607D8B' if not request.GET.get('is_active') else '#9E9E9E',
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
            return format_html('<img src="{}" width="80" style="border-radius:8px;">', obj.preview_image.url)
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

    def action_buttons(self, obj):
        return format_html('''
            <div style="display: flex; gap: 10px;">
                <a href="{}" title="Просмотр" style="background: #007AFF; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">👁</a>
                <a href="{}" title="Редактировать" style="background: #FF9500; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">✏️</a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить {}?')" style="background: #FF3B30; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">🗑</a>
            </div>
        ''',
                f'/admin/kg/kgvehicle/{obj.id}/change/',
                f'/admin/kg/kgvehicle/{obj.id}/change/',
                f'/admin/kg/kgvehicle/{obj.id}/delete/',
            obj.title_display()
        )
    action_buttons.short_description = "Действия"

    def activate_vehicles(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано: {queryset.count()}')
    activate_vehicles.short_description = 'Активировать'

    def deactivate_vehicles(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'❌ Деактивировано: {queryset.count()}')
    deactivate_vehicles.short_description = 'Деактивировать'


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
    list_display = ['name', 'phone', 'region', 'vehicle', 'priority', 'status', 'manager', 'created_at', 'action_buttons']
    list_editable = ['priority', 'status', 'manager']
    list_filter = ['status', 'priority', 'region', 'created_at']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']
    autocomplete_fields = ['vehicle', 'manager']
    date_hierarchy = 'created_at'
    actions = ['export_to_excel']

    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('name', 'phone', 'region', 'vehicle', 'message', 'created_at')
        }),
        ('Управление', {
            'fields': ('status', 'priority', 'manager', 'admin_comment')
        }),
    )
    class Media:
        js = ('admin/js/auto_save_feedback.js',)
        
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Заявки FAW.KG'

        extra_context['status_filters'] = format_html('''
            <div style="margin: 20px 0; display: flex; gap: 12px;">
                <a href="?" style="{}">
                    📊 Все <span style="background: rgba(255,255,255,0.3); padding: 2px 8px; border-radius: 10px; margin-left: 5px;">{}</span>
                </a>
                <a href="?status=new" style="{}">
                    ● Новые <span style="background: rgba(255,255,255,0.3); padding: 2px 8px; border-radius: 10px; margin-left: 5px;">{}</span>
                </a>
                <a href="?status=in_process" style="{}">
                    ◐ В работе <span style="background: rgba(255,255,255,0.3); padding: 2px 8px; border-radius: 10px; margin-left: 5px;">{}</span>
                </a>
                <a href="?status=done" style="{}">
                    ✓ Завершено <span style="background: rgba(255,255,255,0.3); padding: 2px 8px; border-radius: 10px; margin-left: 5px;">{}</span>
                </a>
            </div>
            <style>
                a[href*="status"] {{
                    background: #E5E5EA;
                    color: #1C1C1E;
                    padding: 12px 20px;
                    border-radius: 12px;
                    text-decoration: none;
                    font-weight: 600;
                    transition: all 0.2s;
                }}
                a[href*="status"]:hover {{ 
                    transform: translateY(-2px); 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
                }}
            </style>
        ''',
            'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;' if not request.GET.get('status') else '',
            KGFeedback.objects.count(),
            'background: #34C759; color: white;' if request.GET.get('status') == 'new' else '',
            KGFeedback.objects.filter(status='new').count(),
            'background: #FF9500; color: white;' if request.GET.get('status') == 'in_process' else '',
            KGFeedback.objects.filter(status='in_process').count(),
            'background: #007AFF; color: white;' if request.GET.get('status') == 'done' else '',
            KGFeedback.objects.filter(status='done').count()
        )

        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'status' in request.GET:
            qs = qs.filter(status=request.GET['status'])
        return qs

    def action_buttons(self, obj):
        return format_html('''
            <div style="display: flex; gap: 10px;">
                <a href="{}" title="Просмотр" style="background: #007AFF; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">👁</a>
                <a href="{}" title="Редактировать" style="background: #FF9500; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">✏️</a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить заявку от {}?')" style="background: #FF3B30; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">🗑</a>
            </div>
        ''',
                f'/admin/kg/kgfeedback/{obj.id}/change/',
                f'/admin/kg/kgfeedback/{obj.id}/change/',
                f'/admin/kg/kgfeedback/{obj.id}/delete/',
            obj.name
        )
    action_buttons.short_description = "Действия"

    def export_to_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заявки FAW KG"

        headers = ['№', 'ФИО', 'Телефон', 'Регион', 'Машина', 'Статус', 'Приоритет', 'Менеджер', 'Дата']
        ws.append(headers)

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
            max_length = max(len(str(cell.value)) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="faw_kg_leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response

    export_to_excel.short_description = '📥 Экспорт в Excel'