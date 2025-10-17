from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import KGVehicle, KGVehicleImage, VehicleCardSpec, KGFeedback, KGHeroSlide, IconTemplate
from .forms import VehicleCardSpecForm
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime


# ============================================
# INLINE: ХАРАКТЕРИСТИКИ
# ============================================

class VehicleCardSpecInline(admin.TabularInline):
    model = VehicleCardSpec
    form = VehicleCardSpecForm
    extra = 1
    fields = ('icon_selector', 'icon_preview', 'value_ru', 'order')
    readonly_fields = ('icon_selector', 'icon_preview')
    verbose_name = "Характеристика"
    verbose_name_plural = "Характеристики для каталога"

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="50" style="border-radius:8px;">', obj.icon.url)
        return "—"
    icon_preview.short_description = "Превью"

    def icon_selector(self, obj):
        from .models import IconTemplate
        from django.utils.safestring import mark_safe
        import random
        
        templates = IconTemplate.objects.all().order_by('order')
        
        if not templates.exists():
            return mark_safe('<p style="color:red;">Нет иконок!</p>')
        
        unique_id = f"icon_{random.randint(10000, 99999)}"
        
        html = f'''
        <div id="{unique_id}" style="margin:10px 0;">
            <details style="border:1px solid #ddd; border-radius:5px; padding:5px;">
                <summary style="cursor:pointer; padding:8px; background:#f5f5f5; border-radius:4px; font-weight:600;">
                    Выбрать иконку ({templates.count()})
                </summary>
                <div style="padding:10px; margin-top:10px;">
                    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:8px; max-width:350px;">
        '''
        
        for t in templates:
            html += f'''
            <div class="icon-pick" 
                data-template-id="{t.id}"
                data-icon-url="{t.icon.url}"
                style="text-align:center; padding:8px; border:2px solid #ccc; border-radius:5px; cursor:pointer; background:#fff; transition:all 0.2s;"
                onmouseover="this.style.borderColor='#667eea';"
                onmouseout="this.style.borderColor='#ccc';">
                <img src="{t.icon.url}" width="40" height="40" style="display:block; margin:0 auto 5px;">
                <small style="font-size:9px;">{t.name}</small>
            </div>
            '''
        
        html += f'''
                    </div>
                </div>
            </details>
            <input type="hidden" name="temp_icon" value="" class="selected-icon-input">
        </div>
        
        <script>
        (function() {{
            const container = document.getElementById('{unique_id}');
            const hiddenInput = container.querySelector('.selected-icon-input');
            const iconCards = container.querySelectorAll('.icon-pick');
            
            iconCards.forEach(card => {{
                card.addEventListener('click', function() {{
                    const templateId = this.dataset.templateId;
                    const iconUrl = this.dataset.iconUrl;
                    
                    iconCards.forEach(c => {{
                        c.style.border = '2px solid #ccc';
                        c.style.background = '#fff';
                    }});
                    
                    this.style.border = '3px solid #28a745';
                    this.style.background = '#e8f5e9';
                    
                    const row = container.closest('tr.form-row');
                    const preview = row.querySelector('td:nth-child(2) img');
                    if (preview) {{
                        preview.src = iconUrl;
                        preview.style.display = 'block';
                    }}
                    
                    const inlineGroup = row.closest('.tabular.inline-related');
                    const allRows = inlineGroup.querySelectorAll('tr.form-row');
                    
                    let rowIndex = -1;
                    allRows.forEach((r, index) => {{
                        if (r === row) rowIndex = index;
                    }});
                    
                    if (rowIndex >= 0) {{
                        hiddenInput.name = 'card_specs-' + rowIndex + '-selected_template';
                        hiddenInput.id = 'id_card_specs-' + rowIndex + '-selected_template';
                        hiddenInput.value = templateId;
                    }}
                }});
            }});
        }})();
        </script>
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
        if obj.image:
            return format_html('<img src="{}" width="80" style="border-radius:8px;">', obj.image.url)
        return "Не загружено"
    image_preview.short_description = "Превью"


# ============================================
# ADMIN: КАТАЛОГ МАШИН
# ============================================

@admin.register(KGVehicle)
class KGVehicleAdmin(admin.ModelAdmin):
    list_display = ('mini_thumb', 'title_display', 'category_badge', 'is_active', 'created_at', 'action_buttons')
    list_editable = ('is_active',)
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('title_ru', 'title_ky', 'title_en', 'slug')
    readonly_fields = ('created_at', 'updated_at', 'category')
    inlines = [VehicleCardSpecInline, KGVehicleImageInline]
    list_per_page = 20

    fieldsets = (
        ('Название техники', {
            'fields': ('title_ru', 'title_ky', 'title_en'),
        }),
        ('Фотографии', {
            'fields': ('preview_image', 'main_image')
        }),
        ('Служебная информация', {
            'fields': ('is_active', 'category', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def mini_thumb(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" width="60" style="border-radius:6px;">', obj.preview_image.url)
        return "—"
    mini_thumb.short_description = "Фото"

    def title_display(self, obj):
        return obj.title_ru or obj.title or '—'
    title_display.short_description = "Название"

    def category_badge(self, obj):
        colors = {'v': '#4CAF50', 'vr': '#2196F3', 'vh': '#FF9800'}
        labels = {'v': 'V Series', 'vr': 'VR Series', 'vh': 'VH Series'}
        return format_html(
            '<span style="background:{}; color:white; padding:5px 12px; border-radius:12px; font-weight:600; font-size:11px;">{}</span>',
            colors.get(obj.category, '#757575'), 
            labels.get(obj.category, obj.category.upper())
        )
    category_badge.short_description = "Серия"

    def action_buttons(self, obj):
        return format_html(
            '<div style="display:flex; gap:8px;">'
            '<a href="{}" title="Редактировать" style="display:inline-block; width:28px; height:28px;">'
            '<img src="/static/media/icon-adminpanel/pencil.png" width="28" height="28"></a>'
            '<a href="{}" title="Удалить" onclick="return confirm(\'Удалить {}?\')" style="display:inline-block; width:28px; height:28px;">'
            '<img src="/static/media/icon-adminpanel/recycle-bin.png" width="28" height="28"></a>'
            '<a href="https://faw.kg/vehicle/{}/" target="_blank" title="Посмотреть на сайте" style="display:inline-block; width:28px; height:28px;">'
            '<img src="/static/media/icon-adminpanel/eyes.png" width="28" height="28"></a>'
            '</div>',
            f'/admin/kg/kgvehicle/{obj.id}/change/',
            f'/admin/kg/kgvehicle/{obj.id}/delete/',
            obj.title_ru or 'машину',
            obj.slug
        )
    action_buttons.short_description = "Действия"


# ============================================
# ADMIN: HERO-СЛАЙДЫ
# ============================================

@admin.register(KGHeroSlide)
class KGHeroSlideAdmin(admin.ModelAdmin):
    list_display = ('order', 'vehicle', 'is_active', 'created_at')
    list_display_links = ('vehicle',)
    list_editable = ('is_active', 'order')
    list_filter = ('is_active', 'created_at')
    search_fields = ('vehicle__title_ru', 'description_ru')
    readonly_fields = ('created_at', 'vehicle_preview')

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

    def vehicle_preview(self, obj):
        if obj.vehicle and obj.vehicle.main_image:
            return format_html('<img src="{}" width="200" style="border-radius:8px;">', obj.vehicle.main_image.url)
        elif obj.vehicle and obj.vehicle.preview_image:
            return format_html('<img src="{}" width="200" style="border-radius:8px;">', obj.vehicle.preview_image.url)
        return "—"
    vehicle_preview.short_description = "Превью"


# ============================================
# ADMIN: ЗАЯВКИ
# ============================================

@admin.register(KGFeedback)
class KGFeedbackAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'region', 'vehicle', 'priority', 'status', 'manager', 'created_at']
    list_editable = ['priority', 'status', 'manager']
    list_filter = ['status', 'priority', 'region', 'created_at']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']
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
                feedback.vehicle.title_ru if feedback.vehicle else '-',
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

    export_to_excel.short_description = 'Экспорт в Excel'


# ============================================
# ADMIN: ШАБЛОНЫ ИКОНОК
# ============================================

@admin.register(IconTemplate)
class IconTemplateAdmin(admin.ModelAdmin):
    list_display = ('icon_preview', 'name', 'order')
    list_editable = ('order',)
    fields = ('name', 'icon', 'icon_preview', 'order')
    readonly_fields = ('icon_preview',)
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="60" style="border-radius:8px;">', obj.icon.url)
        return "—"
    icon_preview.short_description = "Превью"