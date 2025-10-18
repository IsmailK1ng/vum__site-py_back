from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline, TranslationStackedInline
from .models import (
    News, NewsBlock, ContactForm, Vacancy, JobApplication, 
    VacancyResponsibility, VacancyRequirement, VacancyCondition, 
    VacancyIdealCandidate,Product, ProductFeature, ProductCardSpec, 
    ProductParameterCategory, ProductParameter, ProductGallery, FeatureTemplate
    )
import openpyxl
from datetime import datetime
from django.http import HttpResponse
from .forms_uz import ProductFeatureForm, ProductCardSpecForm
import random

# Настройка админки
admin.site.site_header = "VUM Admin Panel"
admin.site.site_title = "VUM"
admin.site.index_title = "Управление сайтами FAW"


# ============ ТОЛЬКО FAW.UZ ============

class NewsBlockInline(TranslationTabularInline):
    model = NewsBlock
    extra = 1
    fields = ('block_type', 'text', 'image', 'youtube_url', 'video_file', 'order', 'image_tag')
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="border-radius:8px;">', obj.image.url)
        return "—"
    image_tag.short_description = "Превью"


@admin.register(News)
class NewsAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'author', 'preview_image_tag', 'created_at')
    readonly_fields = ('preview_image_tag', 'author_photo_tag')
    search_fields = ('title', 'author__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    inlines = [NewsBlockInline]

    def preview_image_tag(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" width="100" style="border-radius:8px;">', obj.preview_image.url)
        return "—"
    preview_image_tag.short_description = "Превью"

    def author_photo_tag(self, obj):
        if obj.author_photo:
            return format_html('<img src="{}" width="50" style="border-radius:50%;">', obj.author_photo.url)
        return "—"
    author_photo_tag.short_description = "Фото автора"


@admin.register(ContactForm)
class ContactFormAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'region', 'priority', 'status', 'manager', 'created_at', 'action_buttons']
    list_editable = ['priority', 'status', 'manager']
    list_filter = ['status', 'priority', 'region', 'created_at']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']
    autocomplete_fields = ['manager']
    date_hierarchy = 'created_at'
    actions = ['export_to_excel']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "manager":
            # Убираем все “related links”
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
            formfield.widget.can_view_related = False
        return formfield

    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('name', 'phone', 'region', 'message', 'created_at')
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
        extra_context['title'] = 'Заявки FAW.UZ'

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
            ContactForm.objects.count(),
            'background: #34C759; color: white;' if request.GET.get('status') == 'new' else '',
            ContactForm.objects.filter(status='new').count(),
            'background: #FF9500; color: yellow;' if request.GET.get('status') == 'in_process' else '',
            ContactForm.objects.filter(status='in_process').count(),
            'background: #007AFF; color: green;' if request.GET.get('status') == 'done' else '',
            ContactForm.objects.filter(status='done').count()
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
                <a href="{}" title="Просмотр" style="color: white; width: 35px; height: 35px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none; background: #a5a5a5;">👁</a>
                <a href="{}" title="Редактировать" style="color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none; background: orange;">✏️</a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить заявку от {}?')" style="color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none; background: red;">🗑</a>
            </div>
        ''',
            f'/admin/main/contactform/{obj.id}/change/',
            f'/admin/main/contactform/{obj.id}/change/',
            f'/admin/main/contactform/{obj.id}/delete/',
            obj.name
        )
    action_buttons.short_description = "Действия"

    def export_to_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заявки FAW UZ"

        headers = ['№', 'ФИО', 'Телефон', 'Регион', 'Сообщение', 'Статус', 'Приоритет', 'Менеджер', 'Дата']
        ws.append(headers)

        from openpyxl.styles import Font, PatternFill, Alignment
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        for idx, contact in enumerate(queryset, start=1):
            ws.append([
                idx, 
                contact.name, 
                contact.phone,
                contact.get_region_display(),
                contact.message[:100] if contact.message else '-',
                contact.get_status_display(),
                contact.get_priority_display(),
                contact.manager.username if contact.manager else '-',
                contact.created_at.strftime('%d.%m.%Y %H:%M')
            ])

        for column in ws.columns:
            max_length = max(len(str(cell.value)) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="faw_uz_contacts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response

    export_to_excel.short_description = '📥 Экспорт в Excel'


# Инлайны для вакансий
class VacancyResponsibilityInline(TranslationStackedInline):  # Изменено на TranslationStackedInline
    model = VacancyResponsibility
    extra = 2
    fields = (('title', 'order'), 'text')
    verbose_name = 'Обязанность'
    verbose_name_plural = '📋 Обязанности (с заголовком и описанием)'


class VacancyRequirementInline(TranslationTabularInline):  # Изменено на TranslationTabularInline
    model = VacancyRequirement
    extra = 3
    fields = ('text', 'order')
    verbose_name = 'Требование'
    verbose_name_plural = '✅ Требования к кандидату'


class VacancyConditionInline(TranslationTabularInline):  # Изменено на TranslationTabularInline
    model = VacancyCondition
    extra = 3
    fields = ('text', 'order')
    verbose_name = 'Условие'
    verbose_name_plural = '💼 Условия работы'


class VacancyIdealCandidateInline(TranslationTabularInline):  # Изменено на TranslationTabularInline
    model = VacancyIdealCandidate
    extra = 3
    fields = ('text', 'order')
    verbose_name = 'Качество кандидата'
    verbose_name_plural = '👤 Портрет идеального кандидата'


@admin.register(Vacancy)
class VacancyAdmin(TabbedTranslationAdmin):  # Изменено на TabbedTranslationAdmin
    list_display = ['title', 'is_active', 'applications_count', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'applications_count']
    inlines = [
        VacancyResponsibilityInline,
        VacancyRequirementInline,
        VacancyIdealCandidateInline,
        VacancyConditionInline
    ]
    
    fieldsets = (
        ('📋 Основная информация', {
            'fields': (
                'title',
                'slug',
                'short_description',
                'is_active',
                'order'
            )
        }),
        ('📞 Контактная информация', {
            'fields': ('contact_info',),
            'description': '⚠️ По умолчанию: резюме на hh.uz или info@faw.uz'
        }),
        ('📊 Статистика', {
            'fields': ('applications_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def applications_count(self, obj):
        count = obj.get_applications_count()
        if count > 0:
            return format_html(
                '<a href="/admin/main/jobapplication/?vacancy__id__exact={}" style="color:#007bff;font-weight:bold;">📋 {} заявок</a>',
                obj.id, count
            )
        return '0 заявок'
    applications_count.short_description = 'Заявки'

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['vacancy', 'region', 'applicant_name', 'resume_link', 'file_size_display', 'created_at', 'is_processed_badge']
    list_filter = ['is_processed', 'vacancy', 'region', 'created_at']
    search_fields = ['applicant_name', 'applicant_phone', 'applicant_email', 'admin_comment', 'vacancy__title']
    readonly_fields = ['created_at', 'file_size_display', 'resume_preview']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['vacancy']
    
    fieldsets = (
        ('📋 Информация о заявке', {
            'fields': ('vacancy', 'region', 'created_at')
        }),
        ('📄 Резюме', {
            'fields': ('resume', 'file_size_display', 'resume_preview')
        }),
        ('👤 Контакты кандидата', {
            'fields': ('applicant_name', 'applicant_phone', 'applicant_email')
        }),
        ('✅ Обработка', {
            'fields': ('is_processed', 'admin_comment'),
            'classes': ('wide',)
        }),
    )
    
    actions = ['mark_as_processed', 'export_to_excel']
    
    def resume_link(self, obj):
        if obj.resume:
            return format_html(
                '<a href="{}" target="_blank" style="color:#007bff;font-weight:bold;">📥 Скачать</a>',
                obj.resume.url
            )
        return "—"
    resume_link.short_description = 'Резюме'
    
    def file_size_display(self, obj):
        size = obj.get_file_size()
        if size:
            return f"{size} MB"
        return "—"
    file_size_display.short_description = 'Размер файла'
    
    def resume_preview(self, obj):
        if obj.resume:
            file_ext = obj.resume.name.split('.')[-1].lower()
            if file_ext in ['jpg', 'jpeg', 'png']:
                return format_html('<img src="{}" width="300" style="border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">', obj.resume.url)
            return format_html('<p style="color:#888;">📄 {}</p>', obj.resume.name)
        return "—"
    resume_preview.short_description = 'Превью'
    
    def is_processed_badge(self, obj):
        if obj.is_processed:
            return format_html('<span style="color:green;font-weight:bold;">✅ Рассмотрено</span>')
        return format_html('<span style="color:orange;font-weight:bold;">⏳ Новая</span>')
    is_processed_badge.short_description = 'Статус'
    
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(is_processed=True)
        self.message_user(request, f'✅ {updated} заявок отмечено как рассмотренные.')
    mark_as_processed.short_description = '✅ Отметить как рассмотренные'
    
    def export_to_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заявки на вакансии"
        
        headers = ['№', 'Вакансия', 'Регион', 'ФИО', 'Телефон', 'Email', 'Файл резюме', 'Дата', 'Рассмотрено']
        ws.append(headers)
        
        from openpyxl.styles import Font, PatternFill, Alignment
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for idx, app in enumerate(queryset, start=1):
            ws.append([
                idx,
                app.vacancy.title,
                app.get_region_display(),
                app.applicant_name or '-',
                app.applicant_phone or '-',
                app.applicant_email or '-',
                app.resume.name if app.resume else '-',
                app.created_at.strftime('%d.%m.%Y %H:%M'),
                'Да' if app.is_processed else 'Нет'
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
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="faw_applications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response
    
    export_to_excel.short_description = '📊 Экспорт в Excel'


# ========== ШАБЛОНЫ ХАРАКТЕРИСТИК ==========
@admin.register(FeatureTemplate)
class FeatureTemplateAdmin(TabbedTranslationAdmin):
    list_display = ['icon_preview', 'name', 'category', 'order']
    list_editable = ['name', 'category', 'order']
    list_filter = ['category']
    search_fields = ['name']
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" height="30"/>', obj.icon.url)
        return "—"
    icon_preview.short_description = "Иконка"


# ========== ИНЛАЙНЫ ДЛЯ ПРОДУКТОВ ==========
class ProductFeatureInline(TranslationTabularInline):
    model = ProductFeature
    form = ProductFeatureForm
    extra = 1
    fields = ('icon_selector', 'icon_preview', 'name', 'value', 'order')
    readonly_fields = ('icon_selector', 'icon_preview')
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="40" style="border-radius:4px;"/>', obj.icon.url)
        return "—"
    icon_preview.short_description = "Превью"
    
    def icon_selector(self, obj):
        templates = FeatureTemplate.objects.all().order_by('category', 'order')
        
        if not templates.exists():
            return mark_safe('<p style="color:red;">Добавьте шаблоны иконок!</p>')
        
        widget_id = f"feature_widget_{random.randint(100000, 999999)}"
        
        # Группируем по категориям
        categories = {}
        for t in templates:
            cat = t.category or 'Без категории'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(t)
        
        html = f'''
        <div class="icon-selector-widget" data-widget-id="{widget_id}">
            <details style="border:1px solid #ddd;border-radius:4px;padding:5px;">
                <summary style="cursor:pointer;padding:5px;background:#f0f0f0;">
                    Выбрать иконку ({templates.count()})
                </summary>
                <div style="padding:10px;max-height:300px;overflow-y:auto;">
        '''
        
        for cat_name, cat_templates in categories.items():
            html += f'<h4 style="margin:10px 0 5px;color:#666;">{cat_name}</h4>'
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(70px,1fr));gap:5px;">'
            
            for t in cat_templates:
                html += f'''
                <div class="icon-card" data-template-id="{t.id}" data-icon-url="{t.icon.url}"
                     data-template-name="{t.name}"
                     style="padding:5px;border:1px solid #ddd;border-radius:4px;cursor:pointer;text-align:center;">
                    <img src="{t.icon.url}" width="30" height="30"/>
                    <div style="font-size:9px;margin-top:2px;">{t.name[:10]}</div>
                </div>
                '''
            html += '</div>'
        
        html += f'''
            </div>
        </details>
        <input type="hidden" class="selected-icon-field" name="temp_icon" value="">
        </div>
        
        <script>
        (function() {{
            const widget = document.querySelector('[data-widget-id="{widget_id}"]');
            if (!widget) return;
            
            const hiddenInput = widget.querySelector('.selected-icon-field');
            
            function getRowIndex() {{
                const row = widget.closest('tr');
                if (!row) return -1;
                const tbody = row.parentElement;
                return Array.from(tbody.querySelectorAll('tr')).indexOf(row);
            }}
            
            widget.addEventListener('click', function(e) {{
                const card = e.target.closest('.icon-card');
                if (!card) return;
                
                const rowIndex = getRowIndex();
                hiddenInput.name = `features-${{rowIndex}}-selected_template`;
                hiddenInput.value = card.dataset.templateId;
                
                // Заполняем название
                const nameInput = widget.closest('tr').querySelector('input[id*="name"]');
                if (nameInput && !nameInput.value) {{
                    nameInput.value = card.dataset.templateName;
                }}
                
                // Визуальное выделение
                widget.querySelectorAll('.icon-card').forEach(c => {{
                    c.style.background = '#fff';
                }});
                card.style.background = '#e8f5e9';
                
                // Обновляем превью
                const previewImg = widget.closest('tr').querySelector('.field-icon_preview img');
                if (previewImg) {{
                    previewImg.src = card.dataset.iconUrl;
                }}
            }});
        }})();
        </script>
        '''
        
        return mark_safe(html)
    icon_selector.short_description = "Выбор иконки"


class ProductCardSpecInline(TranslationTabularInline):
    model = ProductCardSpec
    form = ProductCardSpecForm
    extra = 4
    max_num = 4
    fields = ('icon_selector', 'icon_preview', 'value', 'order')
    readonly_fields = ('icon_selector', 'icon_preview')
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="40"/>', obj.icon.url)
        return "—"
    icon_preview.short_description = "Иконка"
    
    def icon_selector(self, obj):
        # Аналогично ProductFeatureInline, но с card_specs вместо features
        templates = FeatureTemplate.objects.all().order_by('category', 'order')
        
        if not templates.exists():
            return mark_safe('<p style="color:red;">Добавьте шаблоны иконок!</p>')
        
        widget_id = f"card_widget_{random.randint(100000, 999999)}"
        
        html = f'''
        <div data-widget-id="{widget_id}">
            <select class="icon-select" style="width:100%;">
                <option value="">-- Выбрать иконку --</option>
        '''
        
        current_cat = None
        for t in templates:
            if t.category != current_cat:
                if current_cat is not None:
                    html += '</optgroup>'
                html += f'<optgroup label="{t.category or "Без категории"}">'
                current_cat = t.category
            html += f'<option value="{t.id}" data-icon="{t.icon.url}">{t.name}</option>'
        
        if current_cat is not None:
            html += '</optgroup>'
        
        html += f'''
            </select>
            <input type="hidden" class="selected-icon-field" value="">
        </div>
        
        <script>
        (function() {{
            const widget = document.querySelector('[data-widget-id="{widget_id}"]');
            const select = widget.querySelector('.icon-select');
            const hidden = widget.querySelector('.selected-icon-field');
            
            function getRowIndex() {{
                const row = widget.closest('tr');
                const tbody = row.parentElement;
                return Array.from(tbody.querySelectorAll('tr')).indexOf(row);
            }}
            
            select.addEventListener('change', function() {{
                const rowIndex = getRowIndex();
                hidden.name = `card_specs-${{rowIndex}}-selected_template`;
                hidden.value = this.value;
                
                const option = this.options[this.selectedIndex];
                const iconUrl = option.dataset.icon;
                
                if (iconUrl) {{
                    const preview = widget.closest('tr').querySelector('.field-icon_preview img');
                    if (preview) preview.src = iconUrl;
                }}
            }});
        }})();
        </script>
        '''
        
        return mark_safe(html)
    icon_selector.short_description = "Выбрать"


class ProductParameterInline(TranslationTabularInline):
    model = ProductParameter
    extra = 3
    fields = ('name', 'value', 'order')


class ProductParameterCategoryInline(TranslationTabularInline):
    model = ProductParameterCategory
    extra = 1
    fields = ('title', 'is_expanded', 'order')


class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 3
    fields = ('image', 'preview', 'order')
    readonly_fields = ('preview',)
    
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="60"/>', obj.image.url)
        return "—"
    preview.short_description = "Превью"


# ========== АДМИНКА ПРОДУКТОВ ==========
@admin.register(Product)
class ProductAdmin(TabbedTranslationAdmin):
    list_display = ['thumbnail', 'title', 'category', 'wheel_formula', 'load_capacity', 'is_active', 'order']
    list_filter = ['category', 'is_active', 'is_featured']
    search_fields = ['title', 'short_description']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                ('title', 'slug'),
                ('category', 'order'),
                ('is_active', 'is_featured'),
            )
        }),
        ('Описания', {
            'fields': ('short_description', 'main_description', 'slogan')
        }),
        ('Изображения', {
            'fields': ('main_image', 'card_image')
        }),
        ('Базовые характеристики', {
            'fields': ('wheel_formula', 'fuel_type', 'load_capacity')
        }),
    )
    
    inlines = [
        ProductFeatureInline,
        ProductCardSpecInline,
        ProductParameterCategoryInline,
        ProductGalleryInline,
    ]
    
    def thumbnail(self, obj):
        img = obj.card_image or obj.main_image
        if img:
            return format_html('<img src="{}" width="80" height="50" style="object-fit:cover;"/>', img.url)
        return "—"
    thumbnail.short_description = "Фото"


# Отдельная админка для параметров (опционально)
@admin.register(ProductParameter)
class ProductParameterAdmin(TabbedTranslationAdmin):
    list_display = ['get_product', 'get_category', 'name', 'value', 'order']
    list_filter = ['category__product', 'category']
    list_editable = ['order']
    
    def get_product(self, obj):
        return obj.category.product.title
    get_product.short_description = "Продукт"
    
    def get_category(self, obj):
        return obj.category.title
    get_category.short_description = "Категория"