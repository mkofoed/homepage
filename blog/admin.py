from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from blog.models import Post


class PostAdmin(MarkdownxModelAdmin):
    list_display = ("title", "date_created", "date_updated", "published")
    list_filter = ("published",)
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Post, PostAdmin)
