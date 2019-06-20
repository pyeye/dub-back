from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .serializers import NewsSerializer, NewsCreateSerializer, CategorySerializer, NewsImageSerializer
from .models import News, Category, NewsImage
from apps.authentication.permissions import IsStaff, IsTokenAuthenticated, IsAdminForDelete
from apps.authentication.backends import OAuth2Authentication
from apps.base.pagination import BasePagination


class AdminNewsViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff)
    pagination_class = BasePagination

    def list(self, request, *args, **kwargs):
        is_active = request.query_params.get('is_active', True) in ['1', 'true', 'True', True]
        queryset = News.objects.filter(is_active=is_active)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NewsSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = NewsSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = NewsCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None, *args, **kwargs):
        model = get_object_or_404(News, pk=pk)
        serializer = NewsSerializer(model)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(News, pk=pk)
        serializer = NewsCreateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @detail_route(methods=['DELETE'])
    def deactivate(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(News, pk=pk)
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['PATCH'])
    def activate(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(News, pk=pk)
        instance.is_active = True
        instance.save()
        return Response(status=status.HTTP_200_OK)


class AdminNewsCategoryViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def list(self, request, *args, **kwargs):
        is_active = request.query_params.get('is_active', True) in ['1', 'true', 'True', True]
        queryset = Category.objects.filter(is_active=is_active)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='PATCH')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)

        if instance.is_active != serializer.initial_data['is_active']:
            raise ValidationError(detail='Операция активации/деактивации не доступна по данному адресу')

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @detail_route(methods=['DELETE'])
    def deactivate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        news = News.objects.filter(category=instance)
        for article in news:
            article.is_active = False
            article.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['PATCH'])
    def activate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = True
        instance.save()

        return Response(status=status.HTTP_200_OK)


class AdminNewsImageViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = NewsImageSerializer
    queryset = NewsImage.objects.all()
