from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline, TranslationStackedInline
from .models import News, NewsBlock, ContactForm, Vacancy, JobApplication, VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate
import openpyxl
from datetime import datetime
from django.http import HttpResponse

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
    list_display = ['name', 'phone', 'region', 'created_at', 'is_processed']
    list_filter = ['is_processed', 'region', 'created_at']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']
    actions = ['mark_as_processed']

    fieldsets = (
        ('Информация о заявке', {
            'fields': ('name', 'phone', 'region', 'message', 'created_at')
        }),
        ('Обработка', {
            'fields': ('is_processed', 'admin_comment')
        }),
    )

    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)
        self.message_user(request, f'Обработано: {queryset.count()}')
    mark_as_processed.short_description = 'Пометить как обработанные'



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
