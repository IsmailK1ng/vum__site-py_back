from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline, TranslationStackedInline
from .models import (
    News, NewsBlock, ContactForm, Vacancy, JobApplication, 
    VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate,
    Product, ProductFeature, ProductCardSpec, ProductGallery, ProductSpecificationGroup, ProductParameter,
    FeatureIcon, SpecificationCategory
)
import nested_admin
import openpyxl
from datetime import datetime
from django.http import HttpResponse

admin.site.site_header = "VUM Admin Panel"
admin.site.site_title = "VUM"
admin.site.index_title = "Управление сайтами FAW"


# ============ НОВОСТИ ============

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


# ============ ЗАЯВКИ ============

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
    
    def action_buttons(self, obj):
        return format_html('''
            <div style="display: flex; gap: 10px;">
                <a href="{}" title="Редактировать" style="color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none; background: orange;">✏️</a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить заявку от {}?')" style="color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-decoration: none; background: red;">🗑</a>
            </div>
        ''',
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
                idx, contact.name, contact.phone, contact.get_region_display(),
                contact.message[:100] if contact.message else '-',
                contact.get_status_display(), contact.get_priority_display(),
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


# ============ ВАКАНСИИ ============

class VacancyResponsibilityInline(TranslationStackedInline):
    model = VacancyResponsibility
    extra = 2
    fields = (('title', 'order'), 'text')


class VacancyRequirementInline(TranslationTabularInline):
    model = VacancyRequirement
    extra = 3
    fields = ('text', 'order')


class VacancyConditionInline(TranslationTabularInline):
    model = VacancyCondition
    extra = 3
    fields = ('text', 'order')


class VacancyIdealCandidateInline(TranslationTabularInline):
    model = VacancyIdealCandidate
    extra = 3
    fields = ('text', 'order')


@admin.register(Vacancy)
class VacancyAdmin(TabbedTranslationAdmin):
    list_display = ['title', 'is_active', 'applications_count', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'applications_count']
    inlines = [VacancyResponsibilityInline, VacancyRequirementInline, VacancyIdealCandidateInline, VacancyConditionInline]
    
    fieldsets = (
        ('📋 Основная информация', {
            'fields': ('title', 'slug', 'short_description', 'is_active', 'order')
        }),
        ('📞 Контактная информация', {
            'fields': ('contact_info',)
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
    search_fields = ['applicant_name', 'applicant_phone', 'applicant_email', 'vacancy__title']
    readonly_fields = ['created_at', 'file_size_display', 'resume_preview']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['vacancy']
    
    fieldsets = (
        ('📋 Информация о заявке', {'fields': ('vacancy', 'region', 'created_at')}),
        ('📄 Резюме', {'fields': ('resume', 'file_size_display', 'resume_preview')}),
        ('👤 Контакты кандидата', {'fields': ('applicant_name', 'applicant_phone', 'applicant_email')}),
        ('✅ Обработка', {'fields': ('is_processed', 'admin_comment'), 'classes': ('wide',)}),
    )
    
    def resume_link(self, obj):
        if obj.resume:
            return format_html('<a href="{}" target="_blank" style="color:#007bff;font-weight:bold;">📥 Скачать</a>', obj.resume.url)
        return "—"
    resume_link.short_description = 'Резюме'
    
    def file_size_display(self, obj):
        size = obj.get_file_size()
        return f"{size} MB" if size else "—"
    file_size_display.short_description = 'Размер файла'
    
    def resume_preview(self, obj):
        if obj.resume:
            file_ext = obj.resume.name.split('.')[-1].lower()
            if file_ext in ['jpg', 'jpeg', 'png']:
                return format_html('<img src="{}" width="300" style="border-radius:8px;">', obj.resume.url)
            return format_html('<p style="color:#888;">📄 {}</p>', obj.resume.name)
        return "—"
    resume_preview.short_description = 'Превью'
    
    def is_processed_badge(self, obj):
        if obj.is_processed:
            return format_html('<span style="color:green;font-weight:bold;">✅ Рассмотрено</span>')
        return format_html('<span style="color:orange;font-weight:bold;">⏳ Новая</span>')
    is_processed_badge.short_description = 'Статус'


# ============ КАТЕГОРИИ ПАРАМЕТРОВ ============

@admin.register(SpecificationCategory)
class SpecificationCategoryAdmin(TabbedTranslationAdmin):
    list_display = ['name', 'slug', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


# ============ ИКОНКИ ============

@admin.register(FeatureIcon)
class FeatureIconAdmin(admin.ModelAdmin):
    list_display = ['icon_preview', 'name', 'order']
    list_editable = ['name', 'order']
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" height="30"/>', obj.icon.url)
        return "—"
    icon_preview.short_description = "Иконка"


# ============ ПРОДУКТЫ - ИНЛАЙНЫ (ОПРЕДЕЛЯЕМ ДО ProductAdmin!) ============

# Миксин для совместимости nested_admin и modeltranslation
class NestedTranslationTabularInline(TranslationTabularInline, nested_admin.NestedTabularInline):
    """Инлайн поддерживающий и вложенность и переводы"""
    pass


class ProductParameterInline(NestedTranslationTabularInline):
    model = ProductParameter
    extra = 1
    fields = ('text', 'order')
    verbose_name = "Параметр"
    verbose_name_plural = "Параметры"


class ProductSpecificationGroupInline(nested_admin.NestedStackedInline):
    model = ProductSpecificationGroup
    extra = 0
    fields = ('category', 'order')
    inlines = [ProductParameterInline]
    verbose_name = "Категория параметров"
    verbose_name_plural = "📋 Параметры продукта (сгруппированные)"
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs["queryset"] = SpecificationCategory.objects.all().order_by('order')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProductFeatureInline(NestedTranslationTabularInline):
    model = ProductFeature
    extra = 8
    max_num = 8
    fields = ('icon', 'name', 'order')
    verbose_name_plural = "🔧 Характеристики с иконками (макс 8)"


class ProductCardSpecInline(NestedTranslationTabularInline):
    model = ProductCardSpec
    extra = 4
    max_num = 4
    fields = ('icon', 'value', 'order')
    verbose_name_plural = "📦 Характеристики для карточки (макс 4)"


class ProductGalleryInline(nested_admin.NestedTabularInline):
    model = ProductGallery
    extra = 3
    verbose_name_plural = "📸 Галерея"


# ============ ПРОДУКТЫ ============

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin, TabbedTranslationAdmin):
    list_display = ['thumbnail', 'title', 'category', 'is_active', 'order']
    list_filter = ['category', 'is_active', 'is_featured']
    search_fields = ['title']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('📋 Основная информация', {
            'fields': (
                ('title', 'slug'),
                ('category', 'order'),
                ('is_active', 'is_featured'),
                # 'short_description',  # ЗАКОММЕНТИРОВАНО
                # 'main_description',   # ЗАКОММЕНТИРОВАНО
                # 'slogan',             # ЗАКОММЕНТИРОВАНО
                ('main_image', 'card_image'),
            )
        }),
    )
    
    inlines = [
        ProductSpecificationGroupInline,  # Группы с параметрами
        ProductFeatureInline,              # Характеристики с иконками
        ProductCardSpecInline,             # Характеристики для карточки
        ProductGalleryInline,              # Галерея
    ]
    
    def thumbnail(self, obj):
        img = obj.card_image or obj.main_image
        if img:
            return format_html('<img src="{}" width="80" height="50" style="object-fit:cover;"/>', img.url)
        return "—"
    thumbnail.short_description = "Фото"