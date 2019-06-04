from django.contrib import admin

from .models import Banner, Advertisement

class BannerAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ['title']
    exclude = ('extra',)


class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ['title']
    exclude = ('extra',)


admin.site.register(Banner, BannerAdmin)
admin.site.register(Advertisement, AdvertisementAdmin)