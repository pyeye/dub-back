from rest_framework import serializers

from .models import News, Category, NewsImage


class NewsImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = NewsImage
        fields = ('pk', 'src')


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('pk', 'name', 'slug', 'is_active')


class NewsSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    image = NewsImageSerializer(read_only=True)

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
            'is_active',
            'image',
            'extra'
        )


class NewsCreateSerializer(serializers.ModelSerializer):

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

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Это поле не может быть пустым.')
