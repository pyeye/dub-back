from rest_framework import viewsets, generics, status
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import BannerSerializer, AdvertisementSerializer
from .models import Banner, Advertisement
from apps.news.models import News
from apps.news.serializers import NewsSerializer
from apps.products.models import ProductInfo
from apps.products.serializers import ProductListSerializer


class BannerApiView(generics.ListAPIView):
    serializer_class = BannerSerializer
    queryset = Banner.objects.all()


class AdvertisementApiView(generics.ListAPIView):
    serializer_class = AdvertisementSerializer
    queryset = Advertisement.objects.all()


class HomeNewsApiView(generics.ListAPIView):
    serializer_class = NewsSerializer
    queryset = News.objects.order_by('-updated_at')[:3]


class BestsellersApiView(generics.ListAPIView):
    queryset = ProductInfo.objects.all()[:10]
    serializer_class = ProductListSerializer


class BestsellersListAPI(APIView):

    def get(self, request, format=None):
        category = 'beer'
        #products = elastic_get_products(category=category)[:6]
        return Response(category, status=status.HTTP_200_OK)