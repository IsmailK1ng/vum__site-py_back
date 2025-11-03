from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render
from django.urls import path
from django import forms
from modeltranslation.admin import TranslationTabularInline, TranslationStackedInline, TabbedTranslationAdmin
from reversion.admin import VersionAdmin
from reversion.models import Version
from .models import (
    News, NewsBlock, ContactForm, Vacancy, 
    VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate,
    JobApplication, FeatureIcon, Product, ProductParameter, ProductFeature, 
    ProductCardSpec, ProductGallery, DealerService, Dealer,
    BecomeADealerPage, DealerRequirement, BecomeADealerApplication
)
import openpyxl
from datetime import datetime
from django.http import HttpResponse

admin.site.site_header = "Панель управления VUM"
admin.site.site_title = "VUM Admin"
admin.site.index_title = "Управление сайтами FAW"


# ============ БАЗОВЫЕ МИКСИНЫ ============

class ContentAdminMixin:
    """Миксин для контент-админов"""
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(
            name__in=['Главные админы', 'Контент-админы']
        ).exists()
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(
            name__in=['Главные админы', 'Контент-админы']
        ).exists()
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Главные админы').exists():
            return True
        
        model_name = self.model._meta.model_name
        perm = f'main.delete_{model_name}'
        return request.user.has_perm(perm)


class LeadManagerMixin:
    """Миксин для лид-менеджеров"""
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(
            name__in=['Главные админы', 'Лид-менеджеры']
        ).exists()
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Главные админы').exists():
            return True
        
        model_name = self.model._meta.model_name
        perm = f'main.delete_{model_name}'
        return request.user.has_perm(perm)


class CustomReversionMixin:
    """Миксин для кастомного шаблона восстановления"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'recover/',
                self.admin_site.admin_view(self.custom_recover_list_view),
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_recoverlist'
            ),
        ]
        return custom_urls + urls
    
    def custom_recover_list_view(self, request):
        """Кастомное представление для списка восстановления"""
        from reversion.models import Version
        from django.conf import settings
        
        opts = self.model._meta
        deleted_versions = Version.objects.get_deleted(self.model)
        
        # Группируем по объектам и берем последнюю версию каждого
        seen_objects = {}
        version_list_with_preview = []
        
        for version in deleted_versions.order_by('-revision__date_created'):
            obj_repr = version.object_repr
            if obj_repr not in seen_objects:
                seen_objects[obj_repr] = True
                
                # Безопасное получение превью
                preview_url = None
                try:
                    field_dict = version.field_dict
                    
                    # Попробуем найти изображение (порядок важен!)
                    for field_name in ['preview_image', 'main_image', 'card_image', 'logo']:
                        if field_name in field_dict and field_dict[field_name]:
                            preview_url = f"{settings.MEDIA_URL}{field_dict[field_name]}"
                            break
                except Exception as e:
                    # Если не удалось получить field_dict - просто пропускаем превью
                    pass
                
                # Добавляем версию с превью в список
                version_list_with_preview.append({
                    'version': version,
                    'preview_url': preview_url,
                    'object_repr': obj_repr,
                    'date': version.revision.date_created
                })
        
        context = {
            **self.admin_site.each_context(request),
            'opts': opts,
            'version_list': version_list_with_preview,
            'title': f'Восстановление: {opts.verbose_name_plural}',
            'has_view_permission': self.has_view_permission(request),
        }
        
        return render(request, 'admin/reversion/recover_list.html', context)

# ============ НОВОСТИ ============

class NewsBlockInline(TranslationStackedInline): 
    model = NewsBlock
    extra = 1
    fields = ('block_type', 'title', 'text', 'image', 'youtube_url', 'video_file', 'order')

    class Media:
        js = ('js/news_block_dynamic.js',)  # ← JS для скрытия полей

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="border-radius:8px;">', obj.image.url)
        return "—"
    image_tag.short_description = "Превью"


@admin.register(News)
class NewsAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    list_display = ['preview_image_tag', 'title', 'author', 'is_active', 'order', 'created_at', 'action_buttons']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'desc']
    readonly_fields = ['preview_image_tag', 'author_photo_tag', 'slug', 'updated_at']
    prepopulated_fields = {}
    inlines = [NewsBlockInline]
    history_latest_first = True
    
    # ← ИСПРАВЛЕННЫЙ ПОРЯДОК FIELDSETS
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'created_at', 'is_active', 'order'),
        }),
        ('Карточка новости', {
            'fields': ('desc', 'preview_image', 'preview_image_tag'),
        }),
        # ← УБРАЛИ "Блоки новостей" отсюда (они уже в inlines)
        ('Автор', {
            'fields': ('author', 'author_photo', 'author_photo_tag')
        }),
        ('Техническая информация', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    # ← ДОБАВИТЬ КАСТОМНЫЙ JS ДЛЯ ДИНАМИЧЕСКИХ ПОЛЕЙ
    class Media:
        js = ('js/admin/news_block_dynamic.js',)

    def preview_image_tag(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" width="100" style="border-radius:8px;"/>', obj.preview_image.url)
        return "—"
    preview_image_tag.short_description = "Превью"

    def author_photo_tag(self, obj):
        if obj.author_photo:
            return format_html('<img src="{}" width="50" style="border-radius:50%;">', obj.author_photo.url)
        return "—"
    author_photo_tag.short_description = "Фото автора"
    
    def action_buttons(self, obj):
        return format_html('''
            <div style="display: flex; gap: 8px;">
                <a href="{}" title="Редактировать">
                    <img src="/static/media/icon-adminpanel/pencil.png" width="24" height="24">
                </a>
                <a href="/news/{}/" title="Просмотр" target="_blank">
                    <img src="/static/media/icon-adminpanel/eyes.png" width="24" height="24">
                </a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить?')">
                    <img src="/static/media/icon-adminpanel/recycle-bin.png" width="24" height="24">
                </a>
            </div>
        ''', f'/admin/main/news/{obj.id}/change/', obj.slug, f'/admin/main/news/{obj.id}/delete/')
    action_buttons.short_description = "Действия"

# ============ ЗАЯВКИ ============

@admin.register(ContactForm)
class ContactFormAdmin(LeadManagerMixin, admin.ModelAdmin):
    list_display = ['name', 'phone', 'region', 'priority', 'status', 'manager', 'created_at', 'action_buttons']
    list_editable = ['priority', 'status', 'manager']
    list_filter = ['status', 'priority', 'region', 'created_at']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']
    autocomplete_fields = ['manager']
    date_hierarchy = 'created_at'
    actions = ['export_to_excel']

    fieldsets = (
        ('Информация о клиенте', {'fields': ('name', 'phone', 'region', 'message', 'created_at')}),
        ('Управление', {'fields': ('status', 'priority', 'manager', 'admin_comment')}),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "manager":
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
            formfield.widget.can_view_related = False
        return formfield
    
    def action_buttons(self, obj):
        return format_html('''
            <div style="display: flex; gap: 10px;">
                <a href="{}" style="color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: orange;">✏️</a>
                <a href="{}" onclick="return confirm('Удалить?')" style="color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: red;">🗑</a>
            </div>
        ''', f'/admin/main/contactform/{obj.id}/change/', f'/admin/main/contactform/{obj.id}/delete/')
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
    
    export_to_excel.short_description = 'Экспорт в Excel'


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
class VacancyAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    list_display = ['title', 'is_active', 'applications_count', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'applications_count']
    inlines = [VacancyResponsibilityInline, VacancyRequirementInline, VacancyIdealCandidateInline, VacancyConditionInline]
    history_latest_first = True
    
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'slug', 'short_description', 'is_active', 'order')}),
        ('Контакты', {'fields': ('contact_info',)}),
        ('Статистика', {'fields': ('applications_count', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def applications_count(self, obj):
        count = obj.get_applications_count()
        if count > 0:
            return format_html(
                '<a href="/admin/main/jobapplication/?vacancy__id__exact={}" style="color:#007bff;font-weight:bold;"> {} Заявок</a>',
                obj.id, count
            )
        return '0 заявок'
    applications_count.short_description = 'Заявки'


@admin.register(JobApplication)
class JobApplicationAdmin(LeadManagerMixin, admin.ModelAdmin):
    list_display = ['vacancy', 'region', 'applicant_name', 'resume_link', 'file_size_display', 'created_at', 'is_processed_badge']
    list_filter = ['is_processed', 'vacancy', 'region', 'created_at']
    search_fields = ['applicant_name', 'applicant_phone', 'applicant_email', 'vacancy__title']
    readonly_fields = ['created_at', 'file_size_display', 'resume_preview']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['vacancy']
    
    fieldsets = (
        ('Информация', {'fields': ('vacancy', 'region', 'created_at')}),
        ('Резюме', {'fields': ('resume', 'file_size_display', 'resume_preview')}),
        ('Контакты', {'fields': ('applicant_name', 'applicant_phone', 'applicant_email')}),
        ('Обработка', {'fields': ('is_processed', 'admin_comment')}),
    )
    
    def resume_link(self, obj):
        if obj.resume:
            return format_html('<a href="{}" target="_blank" style="color:#007bff;font-weight:bold;"> Скачать</a>', obj.resume.url)
        return "—"
    resume_link.short_description = 'Резюме'
    
    def file_size_display(self, obj):
        size = obj.get_file_size()
        return f"{size} MB" if size else "—"
    file_size_display.short_description = 'Размер'
    
    def resume_preview(self, obj):
        if obj.resume:
            file_ext = obj.resume.name.split('.')[-1].lower()
            if file_ext in ['jpg', 'jpeg', 'png']:
                return format_html('<img src="{}" width="300" style="border-radius:8px;">', obj.resume.url)
            return format_html('<p style="color:#888;"> {}</p>', obj.resume.name)
        return "—"
    resume_preview.short_description = 'Превью'
    
    def is_processed_badge(self, obj):
        if obj.is_processed:
            return format_html('<span style="color:green;font-weight:bold;"> Рассмотрено</span>')
        return format_html('<span style="color:orange;font-weight:bold;"> Новая</span>')
    is_processed_badge.short_description = 'Статус'


# ============ ИКОНКИ ============

@admin.register(FeatureIcon)
class FeatureIconAdmin(ContentAdminMixin, admin.ModelAdmin):
    list_display = ['icon_preview', 'name', 'order']
    list_editable = ['name', 'order']
    search_fields = ['name']
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" height="30"/>', obj.icon.url)
        return "—"
    icon_preview.short_description = "Превью"


# ============ ДИЛЕРЫ ============

@admin.register(DealerService)
class DealerServiceAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    list_display = ['name', 'slug', 'order', 'is_active', 'action_buttons']
    list_editable = ['order', 'is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    history_latest_first = True
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.slug in ['sotuv', 'servis', 'ehtiyot-qismlar']:
            return False
        return super().has_delete_permission(request, obj)
    
    def action_buttons(self, obj):
        is_base = obj.slug in ['sotuv', 'servis', 'ehtiyot-qismlar']
        delete_btn = '<span style="opacity: 0.2;"></span>' if is_base else f'<a href="/admin/main/dealerservice/{obj.id}/delete/" onclick="return confirm(\'Удалить?\')"><img src="/static/media/icon-adminpanel/recycle-bin.png" width="24" height="24"></a>'
        
        return format_html('''
            <div style="display: flex; gap: 8px;">
                <a href="{}"><img src="/static/media/icon-adminpanel/pencil.png" width="24" height="24"></a>
                <a href="/dealers/" target="_blank"><img src="/static/media/icon-adminpanel/eyes.png" width="24" height="24"></a>
                {}
            </div>
        ''', f'/admin/main/dealerservice/{obj.id}/change/', delete_btn)
    action_buttons.short_description = "Действия"


@admin.register(Dealer)
class DealerAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    list_display = ['logo_preview', 'name', 'city', 'phone', 'services_list', 'is_active', 'order', 'action_buttons']
    list_filter = ['is_active', 'city', 'services']
    search_fields = ['name', 'city', 'address', 'manager']
    list_editable = ['is_active', 'order']
    readonly_fields = ['logo_preview', 'created_at', 'updated_at']
    history_latest_first = True
    
    fieldsets = (
        ('Основная информация', {'fields': ('name', 'city', 'address', 'logo', 'logo_preview')}),
        ('Координаты', {'fields': ('latitude', 'longitude')}),
        ('Контакты', {'fields': ('phone', 'email', 'website', 'manager')}),
        ('Рабочее время', {'fields': ('working_hours',)}),
        ('Услуги', {'fields': ('services',)}),
        ('Настройки', {'fields': ('is_active', 'order', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "services":
            kwargs['widget'] = forms.CheckboxSelectMultiple()
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="80" height="50" style="object-fit:contain;border-radius:4px;"/>', obj.logo.url)
        return "—"
    logo_preview.short_description = "Логотип"
    
    def services_list(self, obj):
        services = obj.services.all()
        if services:
            tags = ' '.join([f'<span style="background:#e3f2fd;color:#1976d2;padding:4px 8px;border-radius:4px;font-size:11px;">{s.name}</span>' for s in services])
            return format_html(tags)
        return "—"
    services_list.short_description = "Услуги"
    
    def action_buttons(self, obj):
        return format_html('''
            <div style="display: flex; gap: 8px;">
                <a href="{}"><img src="/static/media/icon-adminpanel/pencil.png" width="24" height="24"></a>
                <a href="/dealers/" target="_blank"><img src="/static/media/icon-adminpanel/eyes.png" width="24" height="24"></a>
                <a href="{}" onclick="return confirm('Удалить?')"><img src="/static/media/icon-adminpanel/recycle-bin.png" width="24" height="24"></a>
            </div>
        ''', f'/admin/main/dealer/{obj.id}/change/', f'/admin/main/dealer/{obj.id}/delete/')
    action_buttons.short_description = "Действия"


# ============ СТРАНИЦА "СТАТЬ ДИЛЕРОМ" ============

class DealerRequirementInline(TranslationTabularInline):
    model = DealerRequirement
    extra = 1
    fields = ('text', 'order')


@admin.register(BecomeADealerPage)
class BecomeADealerPageAdmin(ContentAdminMixin, TabbedTranslationAdmin):
    fieldsets = (
        ('Контент', {'fields': ('title', 'intro_text', 'subtitle', 'important_note')}),
        ('Контакты', {'fields': ('contact_phone', 'contact_email', 'contact_address')}),
    )
    inlines = [DealerRequirementInline]
    
    def has_add_permission(self, request):
        return not BecomeADealerPage.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        obj = BecomeADealerPage.get_instance()
        return self.changeform_view(request, str(obj.pk), '', extra_context)


# ============ ЗАЯВКИ НА ДИЛЕРСТВО ============

class BecomeADealerApplicationForm(forms.ModelForm):
    class Meta:
        model = BecomeADealerApplication
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'manager' in self.fields:
            self.fields['manager'].widget.can_add_related = False
            self.fields['manager'].widget.can_change_related = False
            self.fields['manager'].widget.can_delete_related = False
            self.fields['manager'].widget.can_view_related = False


@admin.register(BecomeADealerApplication)
class BecomeADealerApplicationAdmin(LeadManagerMixin, admin.ModelAdmin):
    form = BecomeADealerApplicationForm
    list_display = ['dealer_badge', 'name', 'company_name', 'phone', 'region', 'experience_years', 'status', 'priority', 'manager', 'created_at', 'action_buttons']
    list_filter = ['status', 'priority', 'region', 'created_at']
    search_fields = ['name', 'company_name', 'phone', 'message']
    list_editable = ['status', 'priority', 'manager']
    readonly_fields = ['created_at']
    autocomplete_fields = ['manager']
    date_hierarchy = 'created_at'
    actions = ['export_to_excel']
    
    fieldsets = (
        ('Заявитель', {'fields': ('name', 'company_name', 'experience_years', 'region', 'phone')}),
        ('Сообщение', {'fields': ('message',)}),
        ('Управление', {'fields': ('status', 'priority', 'manager', 'admin_comment', 'created_at')}),
    )
    
    def dealer_badge(self, obj):
        return format_html('<span style="background:#000;color:white;padding:4px 10px;border-radius:6px;font-size:11px;font-weight:600;">ДИЛЕРСТВО</span>')
    dealer_badge.short_description = "Тип"
    
    def action_buttons(self, obj):
        return format_html('''
            <div style="display: flex; gap: 8px;">
                <a href="{}"><img src="/static/media/icon-adminpanel/pencil.png" width="24" height="24"></a>
                <a href="/become-a-dealer/" target="_blank"><img src="/static/media/icon-adminpanel/eyes.png" width="24" height="24"></a>
                <a href="{}" onclick="return confirm('Удалить?')"><img src="/static/media/icon-adminpanel/recycle-bin.png" width="24" height="24"></a>
            </div>
        ''', f'/admin/main/becomeadealerapplication/{obj.id}/change/', f'/admin/main/becomeadealerapplication/{obj.id}/delete/')
    action_buttons.short_description = "Действия"
    
    def export_to_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заявки на дилерство"
        
        headers = ['№', 'ФИО', 'Компания', 'Опыт', 'Регион', 'Телефон', 'Статус', 'Приоритет', 'Менеджер', 'Дата']
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
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="dealer_applications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response
    
    export_to_excel.short_description = 'Экспорт в Excel'


# ============ ПРОДУКТЫ ============

class ProductParameterInline(TranslationTabularInline):
    model = ProductParameter
    extra = 1
    fields = ('category', 'text', 'order')


class ProductFeatureInline(TranslationTabularInline):
    model = ProductFeature
    extra = 1
    max_num = 8
    fields = ('icon', 'name', 'order')


class ProductCardSpecInline(TranslationTabularInline):
    model = ProductCardSpec
    extra = 1
    max_num = 4
    fields = ('icon', 'value', 'order')


class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1
    fields = ('image', 'order')


@admin.register(Product)
class ProductAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    list_display = ['thumbnail', 'title', 'category', 'is_active', 'is_featured', 'order']
    list_filter = ['category', 'is_active', 'is_featured']
    search_fields = ['title', 'slug']
    list_editable = ['is_active', 'is_featured', 'order']
    prepopulated_fields = {'slug': ('title',)}
    history_latest_first = True
    
    fieldsets = (
        ('Основная информация', {
            'fields': (('title', 'slug'), ('category', 'order'), ('is_active', 'is_featured'), ('main_image', 'card_image'))
        }),
    )
    
    inlines = [ProductParameterInline, ProductFeatureInline, ProductCardSpecInline, ProductGalleryInline]
    
    def thumbnail(self, obj):
        img = obj.card_image or obj.main_image
        if img:
            return format_html('<img src="{}" width="80" height="50" style="object-fit:cover;border-radius:4px;"/>',
                               img.url)
        return "—"
    thumbnail.short_description = "Фото"