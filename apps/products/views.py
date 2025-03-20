from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .serializers import CollectionApiSerializer
from .models import Collection
from . import elastic


class ProductViewSet(ViewSet):
    def list(self, request):
        params = request.query_params
        products = elastic.get_products(params)
        return Response(products, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        product = elastic.get_product_info(pk=pk)
        if product is None:
            return Response("Не найдено", status=status.HTTP_404_NOT_FOUND)
        return Response(product, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="instances/(?P<pk>[^/.]+)")
    def product_instances(self, request, pk=None):
        product_instance = elastic.get_product_instance(pk=pk)
        if product_instance is None:
            return Response("Не найдено", status=status.HTTP_404_NOT_FOUND)
        return Response(product_instance, status=status.HTTP_200_OK)


class TagsListAPI(APIView):
    def get(self, request, format=None):
        params = self.request.query_params
        tags = elastic.get_tags(params)
        return Response(tags, status=status.HTTP_200_OK)


class FacetsListAPI(APIView):
    def get(self, request, format=None):
        params = self.request.query_params
        sfacets, nfacets = elastic.get_facets(params)
        response_data = {"sfacets": sfacets, "nfacets": nfacets}
        return Response(response_data, status=status.HTTP_200_OK)


class FacetAllValuesListAPI(APIView):
    """Default size of values on each string facet is equal 10
    this view load all rest values for specific string facet"""
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
            msg = "Нет доступа к коллекции"
            return Response(data=msg, status=status.HTTP_400_BAD_REQUEST)
        serializer = CollectionApiSerializer(instance)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
