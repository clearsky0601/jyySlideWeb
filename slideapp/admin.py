from django.contrib import admin

# Register your models here.

from .models import Slide, SlideCategory


class SlideCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'created_at', 'updated_at')
    ordering = ('position', 'name')


class SlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'category_ref', 'sort_order', 'created_at', 'updated_at')
    list_filter = ('category_ref',)
    ordering = ('category_ref__position', 'sort_order', '-updated_at')

admin.site.register(SlideCategory, SlideCategoryAdmin)
admin.site.register(Slide, SlideAdmin)
