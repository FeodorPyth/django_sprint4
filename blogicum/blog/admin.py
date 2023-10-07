from django.contrib import admin

from .models import Post, Category, Comment, Location


@admin.register(Post, Category, Comment, Location)
class CommonAdmin(admin.ModelAdmin):
    pass
