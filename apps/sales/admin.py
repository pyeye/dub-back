from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .serializers import SaleSerializer, SaleAdminSerializer, SaleImageSerializer
from .models import Sale, SaleImage
from . import elastic
from apps.authentication.permissions import IsStaff, IsTokenAuthenticated, IsAdminForDelete
from apps.authentication.backends import OAuth2Authentication
from apps.base.pagination import BasePagination


class AdminSaleViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff)
    pagination_class = BasePagination

    def list(self, request, *args, **kwargs):
        is_active = request.query_params.get('is_active', True) in ['1', 'true', 'True', True]
        queryset = Sale.objects.filter(is_active=is_active)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SaleSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SaleSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = SaleAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        elastic.add_sale(instance)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None, *args, **kwargs):
        model = get_object_or_404(Sale, pk=pk)
        serializer = SaleSerializer(model)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Sale, pk=pk)
        serializer = SaleAdminSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        elastic.update_sale(instance)
        return Response(serializer.data)

    @detail_route(methods=['DELETE'])
    def deactivate(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Sale, pk=pk)
        instance.is_active = False
        instance.save()
        elastic.remove_sale(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['PATCH'])
    def activate(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Sale, pk=pk)
        instance.is_active = True
        instance.save()
        elastic.add_sale(instance)
        return Response(status=status.HTTP_200_OK)


class AdminSalesImageViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = SaleImageSerializer
    queryset = SaleImage.objects.all()
