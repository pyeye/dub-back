from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from django.shortcuts import get_object_or_404

from apps.products.models import Collection
from apps.products.serializers import CollectionApiSerializer
from apps.sales.models import Sale
from apps.sales.serializers import SaleApiSerializer
from apps.authentication.permissions import IsStaff, IsTokenAuthenticated, IsAdminForDelete
from apps.authentication.backends import OAuth2Authentication
from apps.base.pagination import BasePagination


class AdminHomeSaleViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff)
    pagination_class = BasePagination

    def list(self, request, *args, **kwargs):
        queryset = Sale.objects.filter(on_home=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SaleApiSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SaleApiSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    def retrieve(self, request, pk=None, *args, **kwargs):
        raise MethodNotAllowed('GET')

    def update(self, request, pk=None, *args, **kwargs):
        raise MethodNotAllowed('PUT')

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE')

    @detail_route(methods=['DELETE'])
    def deactivate(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Sale, pk=pk)
        instance.on_home = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['PATCH'])
    def activate(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Sale, pk=pk)
        instance.on_home = True
        instance.save()
        return Response(status=status.HTTP_200_OK)


class AdminHomeCollectionViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff)
    pagination_class = BasePagination

    def list(self, request, *args, **kwargs):
        queryset = Collection.objects.filter(on_home=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CollectionApiSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CollectionApiSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    def retrieve(self, request, pk=None, *args, **kwargs):
        raise MethodNotAllowed('GET')

    def update(self, request, pk=None, *args, **kwargs):
        raise MethodNotAllowed('PUT')

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE')

    @detail_route(methods=['DELETE'])
    def deactivate(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Collection, pk=pk)
        instance.on_home = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['PATCH'])
    def activate(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Collection, pk=pk)
        instance.on_home = True
        instance.save()
        return Response(status=status.HTTP_200_OK)

