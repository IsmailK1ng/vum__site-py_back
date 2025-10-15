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
    list_display = ('preview_thumb', 'title_display', 'category_badge', 'translation_status', 'is_active', 'created_at', 'action_buttons')
    list_editable = ('is_active',)
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('title_ru', 'title_ky', 'title_en', 'slug')
    prepopulated_fields = {
        'slug': ('title',),
        'slug_ru': ('title_ru',),
        'slug_ky': ('title_ky',),
        'slug_en': ('title_en',)
    }
    readonly_fields = ('preview_thumb', 'main_thumb', 'created_at', 'updated_at', 'category', 'translation_helper', 'specs_helper')
    inlines = [VehicleCardSpecInline, KGVehicleImageInline]
    list_per_page = 20
    actions = ['activate_vehicles', 'deactivate_vehicles', 'copy_ru_to_all']

    fieldsets = (
        ('🚨 ВАЖНО: Заполните хотя бы русский язык!', {
            'fields': ('translation_helper',),
            'classes': ('wide',),
            'description': '''
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                    <strong>📋 Инструкция:</strong><br>
                    1️⃣ <strong>ОБЯЗАТЕЛЬНО</strong> заполните русский язык<br>
                    2️⃣ Кыргызский и английский — по желанию<br>
                    3️⃣ Если не заполните перевод — покажется русский<br>
                    4️⃣ Slug заполнится автоматически
                </div>
            '''
        }),
        ('⚙️ Настройки', {
            'fields': ('is_active', 'category'),
            'description': '<em>Категория определяется автоматически по названию (V, VR, VH)</em>'
        }),
        ('🇷🇺 РУССКИЙ ЯЗЫК (обязательно)', {
            'fields': (('title', 'slug'), ('title_ru', 'slug_ru')),
            'classes': ('wide',),
            'description': '<strong style="color: red;">⚠️ Заполните обязательно!</strong>'
        }),
        ('🇰🇬 КЫРГЫЗСКИЙ ЯЗЫК (опционально)', {
            'fields': (('title_ky', 'slug_ky'),),
            'classes': ('wide', 'collapse'),
            'description': '<em>Если не заполните — покажется русский</em>'
        }),
        ('🇬🇧 АНГЛИЙСКИЙ ЯЗЫК (опционально)', {
            'fields': (('title_en', 'slug_en'),),
            'classes': ('wide', 'collapse'),
            'description': '<em>Если не заполните — покажется русский</em>'
        }),
        ('📸 Изображения', {
            'fields': ('preview_image', 'preview_thumb', 'main_image', 'main_thumb')
        }),
        ('📊 Характеристики', {
            'fields': ('specs_helper', 'specs_ru', 'specs_ky', 'specs_en'),
            'classes': ('collapse',),
            'description': '''
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                    <strong>📝 Формат JSON:</strong><br>
                    <pre style="background: white; padding: 10px; border-radius: 4px;">{
  "wheelFormula": "4x2",
  "fuelType": "Дизель",
  "enginePower": "130",
  "payload": "6920",
  "transmission": "Механика"
}</pre>
                    <strong>⚠️ Важно:</strong> Используйте точно такие же ключи!
                </div>
            '''
        }),
        ('🕐 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def translation_helper(self, obj):
        if not obj.pk:
            return format_html('''
                <div style="background: #d1ecf1; padding: 15px; border-radius: 8px; border: 1px solid #bee5eb;">
                    <h3 style="margin-top: 0;">🎯 Как добавить машину:</h3>
                    <ol style="line-height: 1.8;">
                        <li>Заполните <strong>"Название (RU)"</strong> — например: "FAW Tiger V Бортовой"</li>
                        <li>Slug заполнится автоматически</li>
                        <li>Загрузите фотографии (Preview и Main)</li>
                        <li>Заполните характеристики в формате JSON</li>
                        <li>Если хотите — добавьте переводы на кыргызский/английский</li>
                    </ol>
                </div>
            ''')
        
        ru = '✅' if obj.title_ru else '❌'
        ky = '✅' if obj.title_ky else '⚠️'
        en = '✅' if obj.title_en else '⚠️'
        
        return format_html('''
            <div style="background: white; padding: 10px; border-radius: 8px; border: 1px solid #ddd;">
                <strong>Статус переводов:</strong><br>
                🇷🇺 Русский: {} {}<br>
                🇰🇬 Кыргызский: {} {}<br>
                🇬🇧 Английский: {} {}
            </div>
        ''', 
            ru, 'Заполнен' if obj.title_ru else 'НЕ ЗАПОЛНЕН',
            ky, 'Заполнен' if obj.title_ky else 'Не заполнен (показывается русский)',
            en, 'Заполнен' if obj.title_en else 'Не заполнен (показывается русский)'
        )
    translation_helper.short_description = "📊 Статус"

    def specs_helper(self, obj):
        return format_html('''
            <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                <button type="button" onclick="copySpecsTemplate()" style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    📋 Скопировать шаблон
                </button>
                <textarea id="specsTemplate" readonly style="width: 100%; height: 150px; margin-top: 10px; font-family: monospace; padding: 10px;">{{
  "wheelFormula": "4x2",
  "fuelType": "Дизель",
  "enginePower": "130",
  "payload": "6920",
  "transmission": "Механика",
  "dimensions": "7330×2350×2560",
  "wheelbase": "3900",
  "curbWeight": "4380",
  "tankVolume": "100"
}}</textarea>
            </div>
            <script>
            function copySpecsTemplate() {{
                const template = document.getElementById('specsTemplate');
                template.select();
                document.execCommand('copy');
                alert('✅ Шаблон скопирован! Вставьте в поле "Характеристики (RU)"');
            }}
            </script>
        ''')
    specs_helper.short_description = "📝 Шаблон"

    def translation_status(self, obj):
        statuses = []
        if obj.title_ru:
            statuses.append('🇷🇺')
        if obj.title_ky:
            statuses.append('🇰🇬')
        if obj.title_en:
            statuses.append('🇬🇧')
        
        if not statuses:
            return format_html('<span style="color: red;">❌ Не заполнено</span>')
        
        return format_html(' '.join(statuses))
    translation_status.short_description = "Языки"

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
        title = obj.title_ru or obj.title or 'машину'
        return format_html('''
            <div style="display: flex; gap: 10px;">
                <a href="{}" title="Редактировать" style="background: #FF9500; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">✏️</a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить {}?')" style="background: #FF3B30; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">🗑</a>
            </div>
        ''',
            f'/admin/kg/kgvehicle/{obj.id}/change/',
            f'/admin/kg/kgvehicle/{obj.id}/delete/',
            title
        )
    action_buttons.short_description = "Действия"

    def activate_vehicles(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано: {queryset.count()}')
    activate_vehicles.short_description = '✅ Активировать'

    def deactivate_vehicles(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'❌ Деактивировано: {queryset.count()}')
    deactivate_vehicles.short_description = '❌ Деактивировать'

    def copy_ru_to_all(self, request, queryset):
        count = 0
        for obj in queryset:
            if obj.title_ru:
                if not obj.title_ky:
                    obj.title_ky = obj.title_ru
                    obj.slug_ky = obj.slug_ru
                if not obj.title_en:
                    obj.title_en = obj.title_ru
                    obj.slug_en = obj.slug_ru
                if not obj.specs_ky:
                    obj.specs_ky = obj.specs_ru
                if not obj.specs_en:
                    obj.specs_en = obj.specs_ru
                obj.save()
                count += 1
        self.message_user(request, f'📋 Скопировано переводов для {count} машин')
    copy_ru_to_all.short_description = '📋 Копировать RU → KY/EN'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Каталог машин FAW.KG'
        return super().changelist_view(request, extra_context)


@admin.register(KGHeroSlide)
class KGHeroSlideAdmin(admin.ModelAdmin):
    list_display = ('order', 'vehicle_info', 'translation_status', 'vehicle_preview', 'is_active', 'created_at')
    list_display_links = ('vehicle_info',)
    list_editable = ('is_active', 'order')
    list_filter = ('is_active', 'created_at')
    search_fields = ('vehicle__title_ru', 'description_ru')
    readonly_fields = ('created_at', 'vehicle_preview', 'translation_status_display')

    fieldsets = (
        ('📋 Инструкция', {
            'fields': ('translation_status_display',),
            'description': '''
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px;">
                    <strong>Как добавить Hero-слайд:</strong><br>
                    1️⃣ Выберите машину из списка<br>
                    2️⃣ Заполните описание на русском (обязательно)<br>
                    3️⃣ При желании — добавьте переводы<br>
                    4️⃣ Укажите порядок (0 = первый слайд)
                </div>
            '''
        }),
        ('Основная информация', {
            'fields': ('vehicle', 'vehicle_preview', 'order', 'is_active')
        }),
        ('🇷🇺 Описание (Русский)', {
            'fields': ('description_ru',),
            'classes': ('wide',),
            'description': '<strong style="color: red;">⚠️ Заполните обязательно!</strong>'
        }),
        ('🇰🇬 Описание (Кыргызский)', {
            'fields': ('description_ky',),
            'classes': ('wide',),
            'description': '<em>Если не заполните — покажется русский</em>'
        }),
        ('🇬🇧 Описание (Английский)', {
            'fields': ('description_en',),
            'classes': ('wide',),
            'description': '<em>Если не заполните — покажется русский</em>'
        }),
        ('Дополнительно', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def translation_status_display(self, obj):
        if not obj.pk:
            return "Сначала сохраните слайд"
        
        ru = '✅' if obj.description_ru else '❌'
        ky = '✅' if obj.description_ky else '⚠️'
        en = '✅' if obj.description_en else '⚠️'
        
        return format_html('''
            <div style="background: white; padding: 10px; border-radius: 8px; border: 1px solid #ddd;">
                <strong>Статус переводов:</strong><br>
                🇷🇺 Русский: {} {}<br>
                🇰🇬 Кыргызский: {} {}<br>
                🇬🇧 Английский: {} {}
            </div>
        ''',
            ru, 'Заполнен' if obj.description_ru else 'НЕ ЗАПОЛНЕН',
            ky, 'Заполнен' if obj.description_ky else 'Показывается русский',
            en, 'Заполнен' if obj.description_en else 'Показывается русский'
        )
    translation_status_display.short_description = "Статус"

    def translation_status(self, obj):
        statuses = []
        if obj.description_ru:
            statuses.append('🇷🇺')
        if obj.description_ky:
            statuses.append('🇰🇬')
        if obj.description_en:
            statuses.append('🇬🇧')
        
        return format_html(' '.join(statuses)) if statuses else '❌'
    translation_status.short_description = "Языки"

    def vehicle_info(self, obj):
        return obj.vehicle.title_ru or obj.vehicle.title
    vehicle_info.short_description = "Машина"

    def vehicle_preview(self, obj):
        if obj.vehicle and obj.vehicle.main_image:
            return format_html(
                '<img src="{}" width="200" style="border-radius:8px;"><br><b>{}</b>',
                obj.vehicle.main_image.url, obj.vehicle.title
            )
        elif obj.vehicle and obj.vehicle.preview_image:
            return format_html(
                '<img src="{}" width="200" style="border-radius:8px;"><br><b>{}</b>',
                obj.vehicle.preview_image.url, obj.vehicle.title
            )
        return "—"
    vehicle_preview.short_description = "Превью"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Hero-слайды FAW.KG'
        return super().changelist_view(request, extra_context)


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
                <a href="{}" title="Просмотр" style="color: white; width: 35px; height: 35px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">👁</a>
                <a href="{}" title="Редактировать" style="color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">✏️</a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить заявку от {}?')" style="color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none;">🗑</a>
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