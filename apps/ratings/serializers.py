from rest_framework import serializers

from .models import CustomerRating
from apps.products.serializers import ProductsSerializer


class CustomerRatingListSerializer(serializers.ModelSerializer):
    product = ProductsSerializer(read_only=True)

    class Meta:
        model = CustomerRating
        fields = ('pk', 'product', 'rating')


class CustomerRatingSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerRating
        fields = ('pk', 'product', 'rating')