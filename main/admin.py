from django.contrib import admin
from django.utils.html import format_html
from .models import News, NewsBlock

class NewsBlockInline(admin.TabularInline):  # Можно StackedInline для вертикального вида
    model = NewsBlock
    extra = 1  # показывать один пустой блок для добавления
    fields = ('block_type', 'text', 'image', 'youtube_url', 'video_file', 'order', 'image_tag')
    readonly_fields = ('image_tag',)

    class Media:
        js = ('main/admin.js',)  # путь относительно static/

    def image_tag(self, obj):
        if obj.image and obj.image.name:
            return format_html(
                '<img src="{}" width="100" style="border-radius:8px;">',
                obj.image.url
            )
        return "—"
    image_tag.short_description = "Превью блока"


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'preview_image_tag', 'created_at')
    readonly_fields = ('preview_image_tag', 'author_photo_tag')
    search_fields = ('title', 'author__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    inlines = [NewsBlockInline]  # <-- добавили инлайн

    def preview_image_tag(self, obj):
        if obj.preview_image and obj.preview_image.name:
            return format_html(
                '<img src="{}" width="100" style="border-radius:8px;">',
                obj.preview_image.url
            )
        return "—"
    preview_image_tag.short_description = "Превью"

    def author_photo_tag(self, obj):
        if obj.author_photo and obj.author_photo.name:
            return format_html(
                '<img src="{}" width="50" style="border-radius:50%;">',
                obj.author_photo.url
            )
        return "—"
    author_photo_tag.short_description = "Фото автора"


# @admin.register(NewsBlock)
# class NewsBlockAdmin(admin.ModelAdmin):
#     list_display = ('news', 'order', 'block_type', 'short_text', 'image_tag')
#     ordering = ('news', 'order')
#     raw_id_fields = ('news',)  # безопасно для ForeignKey при большом количестве новостей

#     # readonly_fields только при редактировании, чтобы не ломать курсор
#     def get_readonly_fields(self, request, obj=None):
#         if obj:  # редактирование
#             return ('image_tag',)
#         return ()

#     def image_tag(self, obj):
#         if obj.image and obj.image.name:
#             return format_html(
#                 '<img src="{}" width="100" style="border-radius:8px;">',
#                 obj.image.url
#             )
#         return "—"
#     image_tag.short_description = "Изображение"

#     def short_text(self, obj):
#         if obj.text:
#             return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
#         return "—"
#     short_text.short_description = "Текст"
