from rest_framework import viewsets

from .serializers import NewsSerializer, CategorySerializer
from .models import News, Category
from apps.authentication.permissions import IsStaff, IsTokenAuthenticated
from apps.authentication.backends import OAuth2Authentication


class AdminNewsViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff)
    queryset = News.objects.all()
    serializer_class = NewsSerializer


class NewsCategoriesViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer