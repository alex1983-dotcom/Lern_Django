from django.contrib import admin
from .models import Post, Comment, Image
from mdeditor.widgets import MDEditorWidget
from django.db import models

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'publish', 'status']
    list_filter = ['status', 'created', 'publish', 'author']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']
    formfield_overrides = {
        models.TextField: {'widget': MDEditorWidget},
    }

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'post', 'created', 'active']
    list_filter = ['active', 'created', 'updated']
    search_fields = ['name', 'email', 'body']




@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    search_fields = ['title']
