from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from . import elastic
from apps.products.serializers import QuerySerializer


class SearchListAPI(APIView):

    def get(self, request, format=None):
        params = QuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        products = elastic.search_products(params.validated_data)
        return Response(products, status=status.HTTP_200_OK)


class CompletionListAPI(APIView):

    def get(self, request, format=None):
        params = QuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        products = elastic.complete_products(params.validated_data)
        return Response(products, status=status.HTTP_200_OK)
