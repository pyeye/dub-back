from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError

from .serializers import CategorySerializer
from .models import ProductInfo, Category
from . import elastic


class ProductListAPI(APIView):

    def get(self, request, format=None):
        params = self.request.query_params
        products = elastic.get_products(params)
        return Response(products, status=status.HTTP_200_OK)


class ProductDetailAPI(APIView):

    def get(self, request, pk, format=None):
        product = elastic.get_product(pk=pk)
        return Response(product, status=status.HTTP_200_OK)


class TagsListAPI(APIView):

    def get(self, request, format=None):
        category = self.request.query_params.get('category', None)
        tags = elastic.get_tags(category=category)
        return Response(tags, status=status.HTTP_200_OK)


class FacetsListAPI(APIView):

    def get(self, request, format=None):
        params = self.request.query_params
        sfacets, nfacets, = elastic.get_facets(params)
        return Response({ 'sfacets': sfacets, 'nfacets': nfacets }, status=status.HTTP_200_OK)


class CategoryAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    

