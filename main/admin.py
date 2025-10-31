from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline, TranslationStackedInline, TabbedTranslationAdmin
from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline
from .models import (
    News, NewsBlock, ContactForm, Vacancy, 
    VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate,
    JobApplication, FeatureIcon, Product, ProductParameter, ProductFeature, 
    ProductCardSpec, ProductGallery, DealerService, Dealer,
    BecomeADealerPage, DealerRequirement, BecomeADealerApplication
)
import nested_admin
import openpyxl
from datetime import datetime
from django.http import HttpResponse

admin.site.site_header = "Панель управления VUM"
admin.site.site_title = "VUM Admin"
admin.site.index_title = "Управление сайтами FAW"


# ============ НОВОСТИ ============

class NewsBlockInline(TranslationTabularInline):
    model = NewsBlock
    extra = 1
    fields = ('block_type', 'text', 'image', 'youtube_url', 'video_file', 'order', 'image_tag')
    readonly_fields = ('image_tag',)
    verbose_name = "Блок новости"
    verbose_name_plural = "Блоки новости"

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
    verbose_name = "Новость"
    verbose_name_plural = "Новости"

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
    verbose_name = "Заявка с сайта"
    verbose_name_plural = "Заявки с сайта"

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
    verbose_name = "Обязанность"
    verbose_name_plural = "Обязанности"


class VacancyRequirementInline(TranslationTabularInline):
    model = VacancyRequirement
    extra = 3
    fields = ('text', 'order')
    verbose_name = "Требование"
    verbose_name_plural = "Требования"


class VacancyConditionInline(TranslationTabularInline):
    model = VacancyCondition
    extra = 3
    fields = ('text', 'order')
    verbose_name = "Условие"
    verbose_name_plural = "Условия работы"


class VacancyIdealCandidateInline(TranslationTabularInline):
    model = VacancyIdealCandidate
    extra = 3
    fields = ('text', 'order')
    verbose_name = "Качество кандидата"
    verbose_name_plural = "Идеальный кандидат"


@admin.register(Vacancy)
class VacancyAdmin(TabbedTranslationAdmin):
    list_display = ['title', 'is_active', 'applications_count', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'applications_count']
    inlines = [VacancyResponsibilityInline, VacancyRequirementInline, VacancyIdealCandidateInline, VacancyConditionInline]
    verbose_name = "Вакансия"
    verbose_name_plural = "Вакансии"
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'short_description', 'is_active', 'order')
        }),
        ('Контактная информация', {
            'fields': ('contact_info',)
        }),
        ('Статистика', {
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
    verbose_name = "Отклик на вакансию"
    verbose_name_plural = "Отклики на вакансии"
    
    fieldsets = (
        ('Информация о заявке', {'fields': ('vacancy', 'region', 'created_at')}),
        ('Резюме', {'fields': ('resume', 'file_size_display', 'resume_preview')}),
        ('Контакты кандидата', {'fields': ('applicant_name', 'applicant_phone', 'applicant_email')}),
        ('Обработка', {'fields': ('is_processed', 'admin_comment'), 'classes': ('wide',)}),
    )
    
    def resume_link(self, obj):
        if obj.resume:
            return format_html('<a href="{}" target="_blank" style="color:#007bff;font-weight:bold;">📄 Скачать</a>', obj.resume.url)
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
        return format_html('<span style="color:orange;font-weight:bold;">🆕 Новая</span>')
    is_processed_badge.short_description = 'Статус'


# ============ ИКОНКИ ============

@admin.register(FeatureIcon)
class FeatureIconAdmin(admin.ModelAdmin):
    list_display = ['icon_preview', 'name', 'order']
    list_editable = ['name', 'order']
    search_fields = ['name']
    verbose_name = "Иконка"
    verbose_name_plural = "Иконки для характеристик"
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" height="30"/>', obj.icon.url)
        return "—"
    icon_preview.short_description = "Превью"


# ============ ДИЛЕРЫ ============

@admin.register(DealerService)
class DealerServiceAdmin(TabbedTranslationAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    verbose_name = "Услуга дилера"
    verbose_name_plural = "Услуги дилеров"
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.slug in ['sotuv', 'servis', 'ehtiyot-qismlar']:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Dealer)
class DealerAdmin(TabbedTranslationAdmin):
    list_display = [
        'logo_preview', 'name', 'city', 'phone', 
        'services_list', 'is_active', 'order'
    ]
    list_filter = ['is_active', 'city', 'services']
    search_fields = ['name', 'city', 'address', 'manager']
    list_editable = ['is_active', 'order']
    readonly_fields = ['logo_preview', 'created_at', 'updated_at']
    filter_horizontal = ['services']
    verbose_name = "Дилер"
    verbose_name_plural = "Дилеры"
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'city', 'address', 'logo', 'logo_preview')
        }),
        ('Координаты на карте', {
            'fields': ('latitude', 'longitude'),
            'description': 'Получить координаты можно на yandex.uz Яндекс.Картах (ПКМ на точке → "Что здесь?")'
        }),
        ('Контактная информация', {
            'fields': ('phone', 'email', 'website', 'manager')
        }),
        ('Рабочее время', {
            'fields': ('working_hours',),
            'description': 'Используйте &lt;br&gt; для переноса строки. Пример: Пн-Пт: 9:00-20:00&lt;br&gt;Сб: Выходной'
        }),
        ('Услуги', {
            'fields': ('services',)
        }),
        ('Настройки', {
            'fields': ('is_active', 'order', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="80" height="50" style="object-fit:contain;border-radius:4px;"/>',
                obj.logo.url
            )
        return "—"
    logo_preview.short_description = "Логотип"
    
    def services_list(self, obj):
        services = obj.services.all()
        if services:
            tags = ' '.join([
                f'<span style="background:#e3f2fd;color:#1976d2;padding:4px 8px;border-radius:4px;font-size:11px;margin-right:4px;">{s.name}</span>'
                for s in services
            ])
            return format_html(tags)
        return "—"
    services_list.short_description = "Услуги"


# ============ СТРАНИЦА "СТАТЬ ДИЛЕРОМ" ============

class DealerRequirementInline(TranslationTabularInline):
    model = DealerRequirement
    extra = 1
    fields = ('text', 'order')
    verbose_name = "Требование"
    verbose_name_plural = "Список требований"


@admin.register(BecomeADealerPage)
class BecomeADealerPageAdmin(TabbedTranslationAdmin):
    fieldsets = (
        ('Контент страницы', {
            'fields': ('title', 'intro_text', 'subtitle', 'important_note')
        }),
        ('Контактная информация (в форме)', {
            'fields': ('contact_phone', 'contact_email', 'contact_address')
        }),
    )
    
    inlines = [DealerRequirementInline]
    verbose_name = "Страница 'Стать дилером'"
    verbose_name_plural = "Страница 'Стать дилером'"
    
    def has_add_permission(self, request):
        return not BecomeADealerPage.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        obj = BecomeADealerPage.get_instance()
        return self.changeform_view(request, str(obj.pk), '', extra_context)


# ============ ЗАЯВКИ НА ДИЛЕРСТВО ============

@admin.register(BecomeADealerApplication)
class BecomeADealerApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'dealer_badge', 'name', 'company_name', 'phone', 'region', 
        'experience_years', 'status', 'priority', 'manager', 'created_at'
    ]
    list_filter = ['status', 'priority', 'region', 'created_at']
    search_fields = ['name', 'company_name', 'phone', 'message']
    list_editable = ['status', 'priority', 'manager']
    readonly_fields = ['created_at']
    autocomplete_fields = ['manager']
    date_hierarchy = 'created_at'
    actions = ['export_to_excel']
    verbose_name = "Заявка на дилерство"
    verbose_name_plural = "Заявки на дилерство"
    
    fieldsets = (
        ('Информация о заявителе', {
            'fields': ('name', 'company_name', 'experience_years', 'region', 'phone')
        }),
        ('Сообщение', {
            'fields': ('message',)
        }),
        ('Управление заявкой', {
            'fields': ('status', 'priority', 'manager', 'admin_comment', 'created_at')
        }),
    )
    
    def dealer_badge(self, obj):
        return format_html(
            '<span style="background:#ff9800;color:white;padding:4px 10px;border-radius:6px;font-size:11px;font-weight:600;">🤝 ДИЛЕРСТВО</span>'
        )
    dealer_badge.short_description = "Тип"
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "manager":
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
            formfield.widget.can_view_related = False
        return formfield
    
    def export_to_excel(self, request, queryset):
        import openpyxl
        from django.http import HttpResponse
        from datetime import datetime
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заявки на дилерство"
        
        headers = ['№', 'ФИО', 'Компания', 'Опыт (лет)', 'Регион', 'Телефон', 'Статус', 'Приоритет', 'Менеджер', 'Дата']
        ws.append(headers)
        
        from openpyxl.styles import Font, PatternFill, Alignment
        header_fill = PatternFill(start_color='FF9800', end_color='FF9800', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for idx, app in enumerate(queryset, start=1):
            ws.append([
                idx, app.name, app.company_name or '-', app.experience_years or '-',
                app.get_region_display(), app.phone,
                app.get_status_display(), app.get_priority_display(),
                app.manager.username if app.manager else '-',
                app.created_at.strftime('%d.%m.%Y %H:%M')
            ])
        
        for column in ws.columns:
            max_length = max(len(str(cell.value)) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="dealer_applications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response
    
    export_to_excel.short_description = '📥 Экспорт в Excel'


# ============ ПРОДУКТЫ ============

class ProductParameterInline(TranslationTabularInline):
    model = ProductParameter
    extra = 1
    fields = ('category', 'text', 'order')
    verbose_name = "Параметр"
    verbose_name_plural = "Параметры машины"


class ProductFeatureInline(TranslationTabularInline):
    model = ProductFeature
    extra = 1
    max_num = 8
    fields = ('icon', 'name', 'order')
    verbose_name = "Характеристика"
    verbose_name_plural = "Характеристики с иконками (макс 8)"


class ProductCardSpecInline(TranslationTabularInline):
    model = ProductCardSpec
    extra = 1
    max_num = 4
    fields = ('icon', 'value', 'order')
    verbose_name = "Характеристика карточки"
    verbose_name_plural = "Характеристики для карточки (макс 4)"


class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1
    fields = ('image', 'order')
    verbose_name = "Фото"
    verbose_name_plural = "Галерея"


@admin.register(Product)
class ProductAdmin(TabbedTranslationAdmin):
    list_display = ['thumbnail', 'title', 'category', 'is_active', 'is_featured', 'order']
    list_filter = ['category', 'is_active', 'is_featured']
    search_fields = ['title', 'slug']
    list_editable = ['is_active', 'is_featured', 'order']
    prepopulated_fields = {'slug': ('title',)}
    verbose_name = "Продукт"
    verbose_name_plural = "Продукты (грузовики)"
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                ('title', 'slug'),
                ('category', 'order'),
                ('is_active', 'is_featured'),
                ('main_image', 'card_image'),
            )
        }),
    )
    
    inlines = [
        ProductParameterInline,
        ProductFeatureInline,
        ProductCardSpecInline,
        ProductGalleryInline,
    ]
    
    def thumbnail(self, obj):
        img = obj.card_image or obj.main_image
        if img:
            return format_html('<img src="{}" width="80" height="50" style="object-fit:cover;border-radius:4px;"/>', img.url)
        return "—"
    thumbnail.short_description = "Фото"