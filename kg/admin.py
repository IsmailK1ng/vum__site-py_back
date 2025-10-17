from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import KGVehicle, KGVehicleImage, VehicleCardSpec, KGFeedback, KGHeroSlide, IconTemplate
from .forms import VehicleCardSpecForm
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime
from .models import IconTemplate
from django.utils.safestring import mark_safe
import random


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

    class Media:
        js = ('admin/js/icon_selector.js',)

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
            return mark_safe('<p style="color:red;">⚠️ Нет иконок! Добавьте в разделе "Шаблоны иконок"</p>')
        
        # Уникальный ID для этого виджета
        widget_id = f"icon_widget_{random.randint(100000, 999999)}"
        
        html = f'''
        <div class="icon-selector-widget" data-widget-id="{widget_id}">
            <details style="border:1px solid #ddd; border-radius:8px; padding:8px; background:#f9f9f9;">
                <summary style="cursor:pointer; padding:10px; background:#e3f2fd; border-radius:6px; font-weight:600; color:#1976d2;">
                    📦 Выбрать иконку ({templates.count()})
                </summary>
                <div style="padding:15px; margin-top:10px;">
                    <div class="icon-grid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(80px, 1fr)); gap:10px; max-width:100%;">
        '''
        
        for t in templates:
            html += f'''
            <div class="icon-card" 
                data-template-id="{t.id}"
                data-icon-url="{t.icon.url}"
                style="text-align:center; padding:10px; border:2px solid #ddd; border-radius:8px; cursor:pointer; background:#fff; transition:all 0.2s; box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <img src="{t.icon.url}" width="50" height="50" style="display:block; margin:0 auto 8px; object-fit:contain;">
                <small style="font-size:10px; color:#666; display:block; font-weight:500;">{t.name}</small>
            </div>
            '''
        
        html += f'''
                    </div>
                </div>
            </details>
            <input type="hidden" class="selected-icon-field" name="temp_icon" value="">
            <div class="selected-icon-display" style="margin-top:10px; padding:8px; background:#fff; border:1px solid #ddd; border-radius:6px; display:none;">
                <strong style="color:#2e7d32;">✓ Выбрана:</strong> <span class="icon-name"></span>
            </div>
        </div>
        
        <script>
        (function() {{
            const widget = document.querySelector('[data-widget-id="{widget_id}"]');
            if (!widget) return;
            
            const hiddenInput = widget.querySelector('.selected-icon-field');
            const display = widget.querySelector('.selected-icon-display');
            const iconName = widget.querySelector('.icon-name');
            
            // КРИТИЧЕСКАЯ ФУНКЦИЯ: Получаем индекс строки только когда нужно
            function getRowIndex() {{
                const row = widget.closest('tr.form-row');
                if (!row) {{
                    console.error('❌ Строка не найдена для виджета {widget_id}');
                    return -1;
                }}
                
                const table = row.closest('table');
                if (!table) {{
                    console.error('❌ Таблица не найдена');
                    return -1;
                }}
                
                // Получаем ВСЕ строки с формами (включая пустые)
                const allRows = Array.from(table.querySelectorAll('tbody tr.form-row'));
                const index = allRows.indexOf(row);
                
                console.log('🔍 Виджет {widget_id} находится в строке:', index, 'из', allRows.length);
                return index;
            }}
            
            // ЕДИНСТВЕННОЕ место где обновляем name - при клике на иконку
            function updateInputName() {{
                const rowIndex = getRowIndex();
                if (rowIndex >= 0) {{
                    hiddenInput.name = `card_specs-${{rowIndex}}-selected_template`;
                    hiddenInput.id = `id_card_specs-${{rowIndex}}-selected_template`;
                    console.log('✅ Обновлен name для строки', rowIndex, '→', hiddenInput.name);
                }} else {{
                    console.error('❌ Не удалось обновить name, индекс:', rowIndex);
                }}
            }}
            
            // Обработчик выбора иконки
            widget.addEventListener('click', function(e) {{
                const card = e.target.closest('.icon-card');
                if (!card) return;
                
                const templateId = card.dataset.templateId;
                const iconUrl = card.dataset.iconUrl;
                const iconText = card.querySelector('small').textContent;
                
                console.log('🖱️ Клик по иконке:', iconText, 'ID:', templateId);
                
                // СНАЧАЛА обновляем name (КРИТИЧНО!)
                updateInputName();
                
                // ПОТОМ устанавливаем значение
                hiddenInput.value = templateId;
                
                console.log('💾 Установлено значение:', hiddenInput.name, '=', templateId);
                
                // Снимаем выделение со всех карточек
                widget.querySelectorAll('.icon-card').forEach(c => {{
                    c.style.border = '2px solid #ddd';
                    c.style.background = '#fff';
                    c.style.transform = 'scale(1)';
                }});
                
                // Выделяем выбранную
                card.style.border = '3px solid #2e7d32';
                card.style.background = '#e8f5e9';
                card.style.transform = 'scale(1.05)';
                
                // Показываем уведомление
                display.style.display = 'block';
                iconName.textContent = iconText;
                
                // Обновляем превью в таблице
                const row = widget.closest('tr.form-row');
                const previewCell = row.querySelector('td:nth-child(2) img');
                if (previewCell) {{
                    previewCell.src = iconUrl;
                    previewCell.style.border = '2px solid #2e7d32';
                    previewCell.style.borderRadius = '8px';
                }}
                
                console.log('✅ Иконка выбрана успешно');
            }});
            
            console.log('🚀 Виджет {widget_id} инициализирован');
        }})();
        </script>
        
        <style>
        .icon-card:hover {{
            border-color: #64b5f6 !important;
            transform: scale(1.08) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }}
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
        # ВРЕМЕННО: Используем slug_ru
        frontend_url = f"http://localhost:3000/vehicle-details.html?id={obj.slug_ru or obj.slug}&lang=ru"
        
        return format_html(
            '<div style="display:flex; gap:8px;">'
            '<a href="{}" title="Редактировать">'
            '<img src="/static/media/icon-adminpanel/pencil.png" width="28" height="28"></a>'
            '<a href="{}" title="Удалить" onclick="return confirm(\'Удалить {}?\')">'
            '<img src="/static/media/icon-adminpanel/recycle-bin.png" width="28" height="28"></a>'
            '<a href="{}" target="_blank" title="Посмотреть на сайте">'
            '<img src="/static/media/icon-adminpanel/eyes.png" width="28" height="28"></a>'
            '</div>',
            f'/admin/kg/kgvehicle/{obj.id}/change/',
            f'/admin/kg/kgvehicle/{obj.id}/delete/',
            obj.title_ru or 'машину',
            frontend_url
        )
    action_buttons.short_description = "Действия"

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