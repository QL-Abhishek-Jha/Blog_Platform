from django.contrib import admin
from .models import Topic, Blog, Comment, Notification


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display  = ["id", "name", "slug", "created_by", "created_at"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display  = ["id", "title", "author", "topic", "is_published", "published_at", "view_count", "created_at"]
    list_filter   = ["is_published", "topic"]
    search_fields = ["title", "author__username"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ["id", "blog", "user", "is_deleted", "created_at"]
    list_filter   = ["is_deleted"]
    search_fields = ["user__username", "blog__title"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ["id", "user", "blog", "type", "is_read", "created_at"]
    list_filter   = ["type", "is_read"]