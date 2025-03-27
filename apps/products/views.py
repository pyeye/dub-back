from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .serializers import CollectionApiSerializer, QuerySerializer
from .models import Collection
from . import elastic


class ProductViewSet(ViewSet):
    def list(self, request):
        params = QuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        products = elastic.get_products(params.validated_data)
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
        params = QuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        tags = elastic.get_tags(params.validated_data)
        return Response(tags, status=status.HTTP_200_OK)


class FacetsListAPI(APIView):
    def get(self, request, format=None):
        params = QuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        sfacets, nfacets = elastic.get_facets(params.validated_data)
        response_data = {"sfacets": sfacets, "nfacets": nfacets}
        return Response(response_data, status=status.HTTP_200_OK)


class FacetAllValuesListAPI(APIView):
    """Default size of values on each string facet is equal 10
    this view load all rest values for specific string facet
    :query param facet (required): string of the facet values to search for
    """
    def get(self, request, format=None):
        params = QuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        sfacet = self.request.query_params.get('sfacet', None)
        if sfacet is None:
            msg = "'facet' query param is required"
            return Response(data=msg, status=status.HTTP_400_BAD_REQUEST)
        values = elastic.get_sfacet_all_values(params.validated_data, sfacet)
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
