from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.urls import path  
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from modeltranslation.admin import TranslationTabularInline, TranslationStackedInline, TabbedTranslationAdmin
from reversion.admin import VersionAdmin
from reversion.models import Version
from datetime import datetime
from main.models import AmoCRMToken
from main.services.amocrm.token_manager import TokenManager
from .models import (
    News, NewsBlock, ContactForm, Vacancy, 
    VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate,
    JobApplication, FeatureIcon, Product, ProductParameter, ProductFeature, 
    ProductCardSpec, ProductGallery, DealerService, Dealer,
    BecomeADealerPage, DealerRequirement, BecomeADealerApplication,
)
import openpyxl


admin.site.site_header = "Панель управления VUM"
admin.site.site_title = "VUM Admin"
admin.site.index_title = "Управление сайтами FAW"


# ============ БАЗОВЫЕ МИКСИНЫ ============


class ContentAdminMixin:
    """Миксин для контент-админов"""
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        
        # Проверяем группы
        if request.user.groups.filter(
            name__in=['Главные админы', 'Контент-админы', 'Контент UZ', 'Контент UZ+KG']
        ).exists():
            return True
        
        # ✅ ПРОВЕРЯЕМ ИНДИВИДУАЛЬНЫЕ ПРАВА (любое право на просмотр контента)
        content_models = [
            'news', 'product', 'vacancy', 'dealer', 'dealerservice', 
            'featureicon', 'becomeadealerpage'
        ]
        for model in content_models:
            if request.user.has_perm(f'main.view_{model}'):
                return True
        
        return False
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        
        if request.user.groups.filter(
            name__in=['Главные админы', 'Контент-админы', 'Контент UZ', 'Контент UZ+KG']
        ).exists():
            return True
        
        # ✅ ПРОВЕРЯЕМ ИНДИВИДУАЛЬНОЕ ПРАВО на изменение ЭТОЙ модели
        model_name = self.model._meta.model_name
        return request.user.has_perm(f'main.change_{model_name}')
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        
        if request.user.groups.filter(name='Главные админы').exists():
            return True
        
        # ✅ ПРОВЕРЯЕМ ИНДИВИДУАЛЬНОЕ ПРАВО на удаление
        model_name = self.model._meta.model_name
        return request.user.has_perm(f'main.delete_{model_name}')


class LeadManagerMixin:
    """Миксин для лид-менеджеров"""
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        
        # Проверяем группы
        if request.user.groups.filter(
            name__in=['Главные админы', 'Лид-менеджеры', 'Лиды UZ', 'Лиды UZ+KG']
        ).exists():
            return True
        
        # ✅ ПРОВЕРЯЕМ ИНДИВИДУАЛЬНЫЕ ПРАВА (любое право на просмотр заявок)
        lead_models = ['contactform', 'jobapplication', 'becomeadealerapplication']
        for model in lead_models:
            if request.user.has_perm(f'main.view_{model}'):
                return True
        
        return False
    
    def has_add_permission(self, request):
        return False  # Заявки создаются только с фронта
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        
        if request.user.groups.filter(name='Главные админы').exists():
            return True
        
        # ✅ ПРОВЕРЯЕМ ИНДИВИДУАЛЬНОЕ ПРАВО на удаление
        model_name = self.model._meta.model_name
        return request.user.has_perm(f'main.delete_{model_name}')
        
class AmoCRMAdminMixin:
    """Миксин для управления amoCRM"""
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        
        if request.user.groups.filter(name='Главные админы').exists():
            return True
        
        return False
    
    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

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
            path(
                'recover/<int:version_id>/', 
                self.admin_site.admin_view(self.recover_view),  
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_recover'
            ),
        ]
        return custom_urls + urls
    
    def custom_recover_list_view(self, request):
        """Кастомное представление для списка восстановления"""
        from reversion.models import Version
        from django.conf import settings
        
        opts = self.model._meta
        deleted_versions = Version.objects.get_deleted(self.model)
        
        seen_objects = {}
        version_list_with_preview = []
        
        for version in deleted_versions.order_by('-revision__date_created'):
            obj_repr = version.object_repr
            if obj_repr not in seen_objects:
                seen_objects[obj_repr] = True
                
                preview_url = None
                try:
                    field_dict = version.field_dict
                    for field_name in ['preview_image', 'main_image', 'card_image', 'logo']:
                        if field_name in field_dict and field_dict[field_name]:
                            preview_url = f"{settings.MEDIA_URL}{field_dict[field_name]}"
                            break
                except Exception:
                    pass
                
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
    
    def recover_view(self, request, version_id):
        from reversion.models import Version
        from django.contrib import messages
        from django.shortcuts import redirect
        
        opts = self.model._meta
        
        try:
            version = Version.objects.get(pk=version_id)
            
            if version.content_type.model_class() != self.model:
                raise Version.DoesNotExist
            
            version.revision.revert()
            
            messages.success(request, f'✅ Объект "{version.object_repr}" успешно восстановлен!')
            return redirect(f'admin:{opts.app_label}_{opts.model_name}_changelist')
            
        except Version.DoesNotExist:
            messages.error(request, '❌ Версия не найдена или уже восстановлена')
            return redirect(f'admin:{opts.app_label}_{opts.model_name}_recoverlist')
        except Exception as e:
            messages.error(request, f'❌ Ошибка восстановления: {str(e)}')
            return redirect(f'admin:{opts.app_label}_{opts.model_name}_recoverlist')

# ============ НОВОСТИ ============


class NewsBlockInline(TranslationStackedInline): 
    model = NewsBlock
    extra = 1
    fields = ('block_type', 'title', 'text', 'image', 'youtube_url', 'video_file', 'order')

    class Media:
        js = ('js/admin/news_block_dynamic.js',) 
        css = {
            'all': ('css/news_block_custom.css',)  
            
        }


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
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'created_at', 'is_active', 'order'),
        }),
        ('Карточка новости', {
            'fields': ('desc', 'preview_image', 'preview_image_tag'),
        }),
        ('Автор', {
            'fields': ('author', 'author_photo', 'author_photo_tag')
        }),
        ('Техническая информация', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

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
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from reversion.models import Version
        deleted_count = Version.objects.get_deleted(self.model).count()
        if deleted_count > 0:
            extra_context['show_recover_button'] = True
            extra_context['deleted_count'] = deleted_count
        return super().changelist_view(request, extra_context)
    
# ============ ЗАЯВКИ ============

@admin.register(ContactForm)
class ContactFormAdmin(LeadManagerMixin, admin.ModelAdmin):
    change_list_template = 'main/contactform/change_list.html'
    preserve_filters = True
    
    # Оптимизация
    list_select_related = ['manager']
    list_per_page = 50
    show_full_result_count = False
    
    list_display = [
        'name', 'phone', 'product_display', 'region', 
        'priority', 'status', 'amocrm_badge', 
        'manager', 'created_at', 'action_buttons'
    ]
    list_editable = ['priority', 'status', 'manager']  
    list_filter = ['status', 'priority', 'region']
    search_fields = ['name', 'phone', 'amocrm_lead_id']
    readonly_fields = ['created_at', 'amocrm_sent_at', 'amocrm_lead_link']
    autocomplete_fields = ['manager']
    actions = ['retry_failed_leads', 'export_to_excel']

    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('name', 'phone', 'region', 'message', 'created_at')
        }),
        ('Управление', {
            'fields': ('status', 'priority', 'manager', 'admin_comment')
        }),
        ('amoCRM', {
            'fields': ('amocrm_status', 'amocrm_lead_link', 'amocrm_sent_at', 'amocrm_error'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        css = {'all': ('css/amocrm_modal.css', 'css/contactform_admin.css')}
        js = ('js/amocrm_modal.js', 'js/contactform_admin.js')
    
    # ==================== ОТОБРАЖЕНИЕ ====================
    
    def product_display(self, obj):
        if not obj.product:
            return "—"
        return format_html(
            '<span style="color:#1976d2;font-weight:600;">{}</span>',
            obj.product[:30]
        )
        return format_html('<span style="color:#999;">—</span>')
    
    product_display.short_description = "Модель"
    product_display.admin_order_field = 'product'
    
    def amocrm_badge(self, obj):
        """Бейдж статуса amoCRM"""
        if obj.amocrm_status == 'sent':
            return format_html(
                '<span style="background:#10b981;color:white;padding:5px 12px;border-radius:6px;font-weight:600;font-size:12px;">Отправлено</span>'
            )
        elif obj.amocrm_status == 'failed':
            error_text = (obj.amocrm_error or 'Неизвестная ошибка').replace('"', '&quot;').replace("'", '&#39;')
            return format_html(
                '<span class="amocrm-error-badge" data-error="{}" style="background:#ef4444;color:white;padding:5px 12px;border-radius:6px;font-weight:600;font-size:12px;cursor:pointer;" title="Нажмите для просмотра ошибки">Ошибка</span>',
                error_text
            )
        return format_html(
            '<span style="background:#f59e0b;color:white;padding:5px 12px;border-radius:6px;font-weight:600;font-size:12px;">Ожидает</span>'
        )

    amocrm_badge.short_description = "amoCRM"
    amocrm_badge.admin_order_field = 'amocrm_status'
    
    def action_buttons(self, obj):
        """Кнопки действий"""
        view_url = f"https://fawtrucks.amocrm.ru/leads/detail/{obj.amocrm_lead_id}" if obj.amocrm_lead_id else f"/admin/main/contactform/{obj.id}/change/"
        view_title = "Открыть в amoCRM" if obj.amocrm_lead_id else "Просмотр заявки"
        
        return format_html('''
            <div style="display:flex;gap:8px;">
                <a href="{}" title="Редактировать" style="padding:6px;border-radius:6px;display:inline-block;transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                    <img src="/static/media/icon-adminpanel/pencil.png" width="20" height="20">
                </a>
                <a href="{}" title="{}" target="_blank" style="padding:6px;border-radius:6px;display:inline-block;transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                    <img src="/static/media/icon-adminpanel/eyes.png" width="20" height="20">
                </a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить заявку?')" style="padding:6px;border-radius:6px;display:inline-block;transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                    <img src="/static/media/icon-adminpanel/recycle-bin.png" width="20" height="20">
                </a>
            </div>
        ''', f'/admin/main/contactform/{obj.id}/change/', view_url, view_title, f'/admin/main/contactform/{obj.id}/delete/')
    
    action_buttons.short_description = "Действия"
    
    def amocrm_lead_link(self, obj):
        """Ссылка на лид в amoCRM"""
        if obj.amocrm_lead_id:
            url = f"https://fawtrucks.amocrm.ru/leads/detail/{obj.amocrm_lead_id}"
            return format_html(
                '<a href="{}" target="_blank" style="color:#3b82f6;font-weight:600;">Открыть в amoCRM (ID: {})</a>',
                url, obj.amocrm_lead_id
            )
        return "—"
    
    amocrm_lead_link.short_description = "Ссылка на лид"
    
    # ==================== ДЕЙСТВИЯ ====================
    
    def retry_failed_leads(self, request, queryset):
        """Повторная отправка ошибочных заявок"""
        from main.services.amocrm.lead_sender import LeadSender
        import logging
        logger = logging.getLogger('django')
        
        failed_leads = queryset.filter(amocrm_status='failed')
        
        if not failed_leads.exists():
            self.message_user(request, 'Нет ошибочных заявок для повторной отправки', level=messages.WARNING)
            return
        
        success_count = 0
        fail_count = 0
        
        for lead in failed_leads:
            try:
                lead.amocrm_status = 'pending'
                lead.amocrm_error = None
                lead.save()
                
                LeadSender.send_lead(lead)
                lead.refresh_from_db()
                
                if lead.amocrm_status == 'sent':
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"Error retrying lead {lead.id}: {str(e)}", exc_info=True)
                fail_count += 1
        
        if success_count > 0:
            self.message_user(request, f'Успешно отправлено: {success_count}', level=messages.SUCCESS)
        if fail_count > 0:
            self.message_user(request, f'Ошибка отправки: {fail_count}', level=messages.ERROR)
    
    retry_failed_leads.short_description = 'Повторно отправить ошибочные заявки'
    
    def export_to_excel(self, request, queryset):
        """Экспорт в Excel"""
        import logging
        logger = logging.getLogger('django')
        
        try:
            if request.POST.get('select_across') == '1':
                queryset = self.get_queryset(request)
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Заявки FAW UZ"
            
            headers = [
                'Номер', 'ФИО', 'Телефон', 'Модель', 'Регион', 'Сообщение', 
                'Статус', 'Приоритет', 'Менеджер', 'Дата',
                'amoCRM Статус', 'amoCRM ID', 'amoCRM Дата', 'amoCRM Ошибка'
            ]
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
                    contact.product[:30] if contact.product else '-',
                    contact.get_region_display(),
                    contact.message[:100] if contact.message else '-',
                    contact.get_status_display(),
                    contact.get_priority_display(),
                    contact.manager.username if contact.manager else '-',
                    contact.created_at.strftime('%d.%m.%Y %H:%M'),
                    contact.get_amocrm_status_display(),
                    contact.amocrm_lead_id or '-',
                    contact.amocrm_sent_at.strftime('%d.%m.%Y %H:%M') if contact.amocrm_sent_at else '-',
                    contact.amocrm_error[:100] if contact.amocrm_error else '-'
                ])
            
            for column in ws.columns:
                max_length = max(len(str(cell.value)) for cell in column)
                ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
            
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="faw_uz_contacts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            wb.save(response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error exporting to Excel: {str(e)}", exc_info=True)
            self.message_user(request, f'Ошибка экспорта: {str(e)}', level=messages.ERROR)
            return redirect(request.path)
    
    export_to_excel.short_description = 'Экспорт в Excel'
    
    # ==================== QUERYSET ====================
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Отключаем управление менеджерами"""
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "manager":
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
            formfield.widget.can_view_related = False
        return formfield
    
    def get_queryset(self, request):
        """Фильтрация queryset"""
        from django.db.models import Q
        from datetime import datetime
        from django.utils import timezone
        
        qs = super().get_queryset(request)
        
        # Поиск
        if search_query := request.GET.get('q', '').strip():
            qs = qs.filter(
                Q(name__icontains=search_query) | 
                Q(phone__icontains=search_query) | 
                Q(amocrm_lead_id__icontains=search_query)
            )
        
        # Фильтры
        if status := request.GET.get('status', '').strip():
            qs = qs.filter(status=status)
        
        if amocrm_status := request.GET.get('amocrm_status', '').strip():
            qs = qs.filter(amocrm_status=amocrm_status)
        
        if priority := request.GET.get('priority', '').strip():
            qs = qs.filter(priority=priority)
        
        if region := request.GET.get('region', '').strip():
            qs = qs.filter(region=region)
        
        if product := request.GET.get('product', '').strip():
            qs = qs.filter(product__icontains=product)
        
        # Даты
        if date_from := request.GET.get('date_from', '').strip():
            try:
                parsed_date = datetime.strptime(date_from, '%Y-%m-%d')
                date_from_aware = timezone.make_aware(
                    parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
                )
                qs = qs.filter(created_at__gte=date_from_aware)
            except ValueError:
                pass
        
        if date_to := request.GET.get('date_to', '').strip():
            try:
                parsed_date = datetime.strptime(date_to, '%Y-%m-%d')
                date_to_aware = timezone.make_aware(
                    parsed_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                )
                qs = qs.filter(created_at__lte=date_to_aware)
            except ValueError:
                pass
        
        return qs

    def get_changelist(self, request, **kwargs):
        """Переопределяем ChangeList чтобы игнорировать date_from/date_to"""
        from django.contrib.admin.views.main import ChangeList
        
        class CustomChangeList(ChangeList):
            def get_filters_params(self, params=None):
                """Убираем date_from и date_to из lookup параметров"""
                lookup_params = super().get_filters_params(params)
                
                # Удаляем наши кастомные параметры из lookup
                lookup_params.pop('date_from', None)
                lookup_params.pop('date_to', None)
                
                return lookup_params
        
        return CustomChangeList
    
    def changelist_view(self, request, extra_context=None):
        """Контекст для фильтров"""
        extra_context = extra_context or {}
        
        from main.models import REGION_CHOICES
        extra_context['regions'] = REGION_CHOICES
        
        products = ContactForm.objects.exclude(
            product__isnull=True
        ).exclude(
            product=''
        ).values_list('product', flat=True).distinct().order_by('product')
        
        extra_context['products'] = list(products)
        
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/quick-update/', self.admin_site.admin_view(self.quick_update_view), name='contactform_quick_update'),
        ]
        return custom_urls + urls

    def quick_update_view(self, request, object_id):
        """AJAX автосохранение статуса/приоритета/менеджера"""
        import json
        from django.http import JsonResponse
        
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            obj = ContactForm.objects.get(pk=object_id)
            data = json.loads(request.body)
            
            if 'status' in data:
                obj.status = data['status']
            if 'priority' in data:
                obj.priority = data['priority']
            if 'manager' in data:
                obj.manager_id = data['manager'] if data['manager'] else None
            
            obj.save()
            
            return JsonResponse({'success': True})
        
        except ContactForm.DoesNotExist:
            return JsonResponse({'error': 'Object not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
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

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from reversion.models import Version
        deleted_count = Version.objects.get_deleted(self.model).count()
        if deleted_count > 0:
            extra_context['show_recover_button'] = True
            extra_context['deleted_count'] = deleted_count
        return super().changelist_view(request, extra_context)


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
        delete_btn = '🔐' if is_base else f'<a href="/admin/main/dealerservice/{obj.id}/delete/" onclick="return confirm(\'Удалить?\')"><img src="/static/media/icon-adminpanel/recycle-bin.png" width="24" height="24"></a>'
        
        return format_html('''
            <div style="display: flex; gap: 8px;">
                <a href="{}"><img src="/static/media/icon-adminpanel/pencil.png" width="24" height="24"></a>
                <a href="/dealers/" target="_blank"><img src="/static/media/icon-adminpanel/eyes.png" width="24" height="24"></a>
                {}
            </div>
        ''', f'/admin/main/dealerservice/{obj.id}/change/', delete_btn)
    action_buttons.short_description = "Действия"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from reversion.models import Version
        deleted_count = Version.objects.get_deleted(self.model).count()
        if deleted_count > 0:
            extra_context['show_recover_button'] = True
            extra_context['deleted_count'] = deleted_count
        return super().changelist_view(request, extra_context)


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

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from reversion.models import Version
        deleted_count = Version.objects.get_deleted(self.model).count()
        if deleted_count > 0:
            extra_context['show_recover_button'] = True
            extra_context['deleted_count'] = deleted_count
        return super().changelist_view(request, extra_context)

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

# КАСТОМНЫЙ ФИЛЬТР ДЛЯ КАТЕГОРИЙ
class ProductCategoryFilter(admin.SimpleListFilter):
    """Фильтр по категориям с учетом основной и дополнительных"""
    title = 'категория'
    parameter_name = 'category_filter'
    
    def lookups(self, request, model_admin):
        """Возвращаем все доступные категории"""
        return Product.CATEGORY_CHOICES
    
    def queryset(self, request, queryset):
        """Фильтруем по основной И дополнительным категориям"""
        if self.value():
            from django.db.models import Q
            
            # Ищем продукты где:
            # 1. Основная категория совпадает
            # 2. ИЛИ категория есть в дополнительных (через LIKE)
            return queryset.filter(
                Q(category=self.value()) | 
                Q(categories__contains=self.value())
            )
        return queryset

class ProductCategoriesForm(forms.ModelForm):
    """Форма с множественным выбором категорий"""
    selected_categories = forms.MultipleChoiceField(
        choices=Product.CATEGORY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,  # ✅ Обязательно выбрать хотя бы одну
        label="Категории",
        help_text="Выберите одну или несколько категорий, в которых будет отображаться продукт"
    )
    
    class Meta:
        model = Product
        # ✅ Исключаем старые поля из формы
        exclude = ['category', 'categories']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ✅ Предзаполняем выбранные категории
        if self.instance.pk:
            selected = []
            
            # Добавляем основную категорию
            if self.instance.category:
                selected.append(self.instance.category)
            
            # Добавляем дополнительные категории
            if self.instance.categories:
                additional = [cat.strip() for cat in self.instance.categories.split(',') if cat.strip()]
                selected.extend(additional)
            
            # Убираем дубликаты
            selected = list(dict.fromkeys(selected))
            
            self.fields['selected_categories'].initial = selected
    
    def clean_selected_categories(self):
        """Валидация: должна быть выбрана хотя бы одна категория"""
        categories = self.cleaned_data.get('selected_categories', [])
        
        if not categories:
            raise forms.ValidationError("Выберите хотя бы одну категорию")
        
        return categories
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # ✅ Получаем выбранные категории
        selected = self.cleaned_data.get('selected_categories', [])
        
        if selected:
            # Первая категория становится основной
            instance.category = selected[0]
            
            # Остальные категории идут в дополнительные
            if len(selected) > 1:
                instance.categories = ','.join(selected[1:])
            else:
                instance.categories = ''
        
        if commit:
            instance.save()
        return instance


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
    form = ProductCategoriesForm  # ✅ Используем кастомную форму
    
    list_display = ['thumbnail', 'title', 'all_categories_display', 'is_active', 'is_featured', 'slider_order', 'order']
    list_filter = [ProductCategoryFilter, 'is_active', 'is_featured'] 
    search_fields = ['title', 'slug']
    list_editable = ['is_active', 'is_featured', 'slider_order', 'order']
    prepopulated_fields = {'slug': ('title',)}
    history_latest_first = True
    actions = ['add_to_slider', 'remove_from_slider']
    
    list_per_page = 15
    show_full_result_count = False
    list_select_related = []
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                ('title', 'slug'), 
                'selected_categories',  # ✅ Единый чеклист категорий
                ('order', 'is_active', 'is_featured'), 
                ('main_image', 'card_image')
            )
        }),
        ('⭐ Настройки главного слайдера', {
            'classes': ('collapse',),
            'fields': (
                'slider_image',
                ('slider_year', 'slider_order'),
                'slider_price',
                ('slider_power', 'slider_fuel_consumption'),
            ),
        }),
    )
    
    inlines = [ProductParameterInline, ProductFeatureInline, ProductCardSpecInline, ProductGalleryInline]
    
    def thumbnail(self, obj):
        img = obj.card_image or obj.main_image
        if img:
            return format_html(
                '<img src="{}" width="80" height="50" style="object-fit:cover;border-radius:4px;"/>',
                img.url
            )
        return "—"
    thumbnail.short_description = "Фото"
    
    # ✅ Обновленный метод для отображения ВСЕХ категорий
    def all_categories_display(self, obj):
        """Отображение всех категорий продукта"""
        categories = obj.get_all_categories()
        
        if not categories:
            return "—"
        
        # Получаем названия категорий
        category_names = []
        for cat_slug in categories:
            for slug, name in Product.CATEGORY_CHOICES:
                if slug == cat_slug:
                    category_names.append(name)
                    break
        
        if category_names:
            # Первая категория - основная (синий цвет)
            tags = []
            for idx, name in enumerate(category_names):
                if idx == 0:
                    # Основная категория
                    tags.append(
                        f'<span style="background:#1976d2;color:white;padding:4px 8px;border-radius:4px;font-size:11px;font-weight:600;">{name}</span>'
                    )
                else:
                    # Дополнительные категории
                    tags.append(
                        f'<span style="background:#d3ecff;color:#006ad3;padding:4px 8px;border-radius:4px;font-size:11px;font-weight:400;">{name}</span>'
                    )
            
            return format_html(' '.join(tags))
        return "—"
    
    all_categories_display.short_description = "Категории"
    
    def add_to_slider(self, request, queryset):
        """Добавить выбранные продукты в слайдер"""
        updated = queryset.update(is_featured=True)
        self.message_user(
            request, 
            f'✅ {updated} продуктов добавлено в главный слайдер'
        )
    add_to_slider.short_description = '⭐ Добавить в главный слайдер'
    
    def remove_from_slider(self, request, queryset):
        """Убрать выбранные продукты из слайдера"""
        updated = queryset.update(is_featured=False)
        self.message_user(
            request, 
            f'❌ {updated} продуктов убрано из слайдера'
        )
    remove_from_slider.short_description = '❌ Убрать из слайдера'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from reversion.models import Version
        deleted_count = Version.objects.get_deleted(self.model).count()
        if deleted_count > 0:
            extra_context['show_recover_button'] = True
            extra_context['deleted_count'] = deleted_count
        
        # Добавляем информацию о слайдере
        featured_count = Product.objects.filter(is_featured=True, is_active=True).count()
        extra_context['featured_count'] = featured_count
        extra_context['show_slider_info'] = True
        
        return super().changelist_view(request, extra_context)

@admin.register(AmoCRMToken)
class AmoCRMTokenAdmin(AmoCRMAdminMixin, admin.ModelAdmin):
    list_display = ['token_status', 'expires_display', 'time_left_display', 'action_buttons']
    
    # ========== ОТОБРАЖЕНИЕ ==========
    def token_status(self, obj):
        """Статус токена"""
        from django.utils import timezone
        
        if not obj.access_token:
            return format_html(
                '<span style="background:#dc3545;color:white;padding:6px 12px;border-radius:6px;font-weight:600;">Не настроен</span>'
            )
        
        if obj.is_expired():
            return format_html(
                '<span style="background:#ffc107;color:#000;padding:6px 12px;border-radius:6px;font-weight:600;">Истекает скоро</span>'
            )
        
        return format_html(
            '<span style="background:#28a745;color:white;padding:6px 12px;border-radius:6px;font-weight:600;">Валиден</span>'
        )
    
    token_status.short_description = "Статус"
    
    def expires_display(self, obj):
        """Дата истечения"""
        if obj.expires_at:
            return obj.expires_at.strftime('%d.%m.%Y %H:%M')
        return "—"
    
    expires_display.short_description = "Истекает"
    
    def time_left_display(self, obj):
        """Оставшееся время"""
        from django.utils import timezone
        
        if not obj.expires_at:
            return "—"
        
        time_left = obj.expires_at - timezone.now()
        
        if time_left.total_seconds() < 0:
            return format_html('<span style="color:#dc3545;font-weight:600;">Истёк</span>')
        
        days = time_left.days
        hours = int(time_left.seconds / 3600)
        minutes = int((time_left.seconds % 3600) / 60)
        
        if time_left.total_seconds() < 3600:
            color = '#dc3545'
        elif time_left.total_seconds() < 7200:
            color = '#ffc107'
        else:
            color = '#28a745'
        
        if days > 0:
            text = f"{days} дн. {hours} ч."
        elif hours > 0:
            text = f"{hours} ч. {minutes} мин."
        else:
            text = f"{minutes} мин."
        
        return format_html('<span style="color:{};font-weight:600;">{}</span>', color, text)
    
    time_left_display.short_description = "Осталось"
    
    def action_buttons(self, obj):
        """Кнопки действий"""
        return format_html('''
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <a href="/admin/main/amocrmtoken/refresh/" 
                   class="button" 
                   style="background:#007bff;color:white;padding:6px 12px;border-radius:4px;text-decoration:none;white-space:nowrap;">
                    Обновить токен
                </a>
                <a href="/admin/main/amocrmtoken/logs/" 
                   class="button" 
                   style="background:#dc3545;color:white;padding:6px 12px;border-radius:4px;text-decoration:none;white-space:nowrap;">
                    Логи ошибок
                </a>
                <a href="/admin/main/amocrmtoken/instructions/" 
                   class="button" 
                   style="background:#6c757d;color:white;padding:6px 12px;border-radius:4px;text-decoration:none;white-space:nowrap;">
                    Инструкция
                </a>
            </div>
        ''')
    
    action_buttons.short_description = "Действия"
    
    # ========== МАРШРУТЫ ==========
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('refresh/', self.admin_site.admin_view(self.refresh_token_view), name='amocrm_refresh'),
            path('logs/', self.admin_site.admin_view(self.logs_view), name='amocrm_logs'),
            path('instructions/', self.admin_site.admin_view(self.instructions_view), name='amocrm_instructions'),
        ]
        return custom_urls + urls
    
    # ========== ОБРАБОТЧИКИ ==========
    def refresh_token_view(self, request):
        """Обновить токен вручную"""
        try:
            token_obj = AmoCRMToken.get_instance()
            
            if not token_obj.refresh_token:
                messages.error(request, 'Refresh token не найден. Настройте токены заново.')
                return redirect('/admin/main/amocrmtoken/')
            
            TokenManager.refresh_token(token_obj)
            messages.success(request, f'Токен успешно обновлён. Истекает: {token_obj.expires_at.strftime("%d.%m.%Y %H:%M")}')
            
        except Exception as e:
            messages.error(request, f'Ошибка обновления: {str(e)}')
        
        return redirect('/admin/main/amocrmtoken/')
    
    def logs_view(self, request):
        """Показать логи ошибок amoCRM"""
        import os
        from django.conf import settings
        
        amocrm_log_path = os.path.join(settings.BASE_DIR, 'logs', 'amocrm.log')
        errors_log_path = os.path.join(settings.BASE_DIR, 'logs', 'errors.log')
        
        amocrm_logs = []
        errors_logs = []
        
        if os.path.exists(amocrm_log_path):
            try:
                with open(amocrm_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    amocrm_logs = [line.strip() for line in lines if line.strip()][-100:]
            except Exception as e:
                amocrm_logs = [f"Ошибка чтения amocrm.log: {str(e)}"]
        
        if os.path.exists(errors_log_path):
            try:
                with open(errors_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    errors_logs = [line.strip() for line in lines if line.strip()][-50:]
            except Exception as e:
                errors_logs = [f"Ошибка чтения errors.log: {str(e)}"]
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Логи ошибок amoCRM',
            'amocrm_logs': amocrm_logs,
            'errors_logs': errors_logs,
        }
        return render(request, 'main/amocrm_logs.html', context)
    
    def instructions_view(self, request):
        """Показать инструкцию"""
        from django.utils import timezone
        
        token_obj = AmoCRMToken.get_instance()
        time_left_text = None
        
        if token_obj.expires_at:
            time_left = token_obj.expires_at - timezone.now()
            
            if time_left.total_seconds() < 0:
                time_left_text = "Токен истёк"
            else:
                days = time_left.days
                hours = int(time_left.seconds / 3600)
                minutes = int((time_left.seconds % 3600) / 60)
                
                parts = []
                if days > 0:
                    parts.append(f"{days} дн.")
                if hours > 0:
                    parts.append(f"{hours} ч.")
                if minutes > 0:
                    parts.append(f"{minutes} мин.")
                
                time_left_text = " ".join(parts) if parts else "Менее минуты"
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Инструкция: Обновление токенов amoCRM',
            'token': token_obj,
            'time_left_text': time_left_text,
        }
        return render(request, 'main/amocrm_instructions.html', context)