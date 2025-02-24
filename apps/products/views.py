from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .serializers import CollectionApiSerializer, CollectionSerializer, ProductInstanceSerializer, ProductInfoPublicSerializer
from .models import Collection, ProductInfo, ProductInstance
from . import elastic


class ProductListAPI(APIView):

    def get(self, request, format=None):
        params = self.request.query_params
        products = elastic.get_products(params)
        return Response(products, status=status.HTTP_200_OK)


class ProductDetailAPI(APIView):

    def get(self, request, pk, format=None):
        product_info = get_object_or_404(ProductInfo, pk=pk)
        if not product_info.instances:
            return Response('Нет активных товаров', status=status.HTTP_404_NOT_FOUND)
        serializer = ProductInfoPublicSerializer(product_info)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductDetailInstancesAPI(APIView):
    
    def get(self, request, pk, format=None):
        product_info = get_object_or_404(ProductInfo, pk=pk)
        product_instances = product_info.instances.filter(status=ProductInstance.STATUS_ACTIVE)
        serialized_data = ProductInstanceSerializer(product_instances, many=True)
        return Response(serialized_data.data, status=status.HTTP_200_OK)


class TagsListAPI(APIView):

    def get(self, request, format=None):
        params = self.request.query_params
        tags = elastic.get_tags(params)
        return Response(tags, status=status.HTTP_200_OK)


class FacetsListAPI(APIView):

    def get(self, request, format=None):
        params = self.request.query_params
        sfacets, nfacets, = elastic.get_facets(params)
        return Response({ 'sfacets': sfacets, 'nfacets': nfacets }, status=status.HTTP_200_OK)


class FacetAllValuesListAPI(APIView):

    def get(self, request, format=None):
        params = self.request.query_params
        values = elastic.get_all_special_agg_values(params)
        return Response(data=values, status=status.HTTP_200_OK)


class CategoryAPIView(APIView):

    def get(self, request, format=None):
        categories = elastic.get_categories()
        return Response(data=categories, status=status.HTTP_200_OK)


class CollectionDetailAPIView(APIView):

    def get(self, request, pk, format=None):
        instance = get_object_or_404(Collection, pk=pk)
        if not instance.is_active or not instance.is_public:
            return Response(data='Нет доступа к коллекции', status=status.HTTP_400_BAD_REQUEST)
        serializer = CollectionApiSerializer(instance)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
