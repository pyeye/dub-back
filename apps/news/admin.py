from django.contrib import admin
from django.db import models
from pagedown.widgets import AdminPagedownWidget

from .models import News, Category


class NewsAdmin(admin.ModelAdmin):

    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }

    def created_format(self, obj):
        return obj.created_at.strftime("%d.%m.%Y")
    created_format.admin_order_field = 'created'
    created_format.short_description = 'Созданно'

    def updated_format(self, obj):
        return obj.created_at.strftime("%d.%m.%Y")

    updated_format.admin_order_field = 'updated'
    updated_format.short_description = 'Обновленно'

    list_display = ('title', 'created_format', 'updated_format', 'is_active')
    list_editable = ['is_active']
    search_fields = ['title']
    date_hierarchy = 'created_at'


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ['name']

admin.site.register(News, NewsAdmin)
admin.site.register(Category, CategoryAdmin)
