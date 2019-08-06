from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .serializers import NewsSerializer, CategorySerializer
from .models import News, Category


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = News.objects.filter(is_active=True)
    serializer_class = NewsSerializer

    @list_route()
    def categories(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
