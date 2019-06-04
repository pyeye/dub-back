from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .elastic import elastic_search_products, elastic_complete_products


class SearchListAPI(APIView):

    def get(self, request, format=None):
        params = self.request.query_params
        products = elastic_search_products(params)
        return Response(products, status=status.HTTP_200_OK)


class CompletionListAPI(APIView):

    def get(self, request, format=None):
        params = self.request.query_params
        products = elastic_complete_products(params)
        return Response(products, status=status.HTTP_200_OK)