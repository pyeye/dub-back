from rest_framework import serializers

from .models import News, Category


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'code')


class NewsSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = News
        fields = (
            'pk',
            'title',
            'description',
            'category',
            'date_created',
            'date_updated',
            'is_updated',
            'image',
            'extra'
        )
