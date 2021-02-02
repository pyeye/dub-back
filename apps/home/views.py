from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.sales.models import Sale
from apps.sales.serializers import SaleApiSerializer
from apps.news.models import News
from apps.news.serializers import NewsSerializer
from apps.products.models import ProductInfo, Collection
from apps.products.serializers import ProductListSerializer, CollectionApiSerializer
from apps.products import elastic


class HomeSalesAPI(APIView):
    def get(self, request, format=None):
        queryset = Sale.objects.filter(on_home=True)
        serializer = SaleApiSerializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class HomeCollectionAPI(APIView):
    def get(self, request, format=None):
        queryset = Collection.objects.filter(on_home=True, is_active=True)
        serializer = CollectionApiSerializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class HomeNewsApiView(generics.ListAPIView):
    serializer_class = NewsSerializer
    queryset = News.objects.filter(is_active=True).order_by('-updated_at')[:3]


class BestsellersApiView(generics.ListAPIView):
    queryset = ProductInfo.objects.all()[:10]
    serializer_class = ProductListSerializer


class NewProductsListAPI(APIView):

    def get(self, request, format=None):
        params = request.query_params
        products = elastic.get_products(params)
        return Response(products['items'][:10], status=status.HTTP_200_OK)
