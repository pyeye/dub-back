from rest_framework import serializers

from .models import Banner, Advertisement

class BannerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Banner
        fields = ('pk', 'title', 'image', 'url', 'extra')


class AdvertisementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Advertisement
        fields = ('pk', 'title', 'image', 'url', 'extra')
