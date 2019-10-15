from datetime import datetime

import requests
from rest_framework import viewsets, status
from rest_framework.decorators import action
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
        queryset = Sale.objects.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SaleSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SaleSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = SaleAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        # self._create_sale_task(sale)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None, *args, **kwargs):
        model = get_object_or_404(Sale, pk=pk)
        serializer = SaleSerializer(model)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Sale, pk=pk)
        serializer = SaleAdminSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()

        # self._update_sale_task(sale)
        
        return Response(serializer.data)
    
    def _create_sale_task(self, sale):
        now = datetime.now()
        if not sale.is_active or now > sale.date_end:
            return
        
        data = {
            'id': sale.pk,
            'date_start': sale.date.start,
            'date_end': sale.date.end,
            'is_active': sale.is_active,
        }
        
        r = requests.post('http://scheduler:8010/sales', data=data)
    
    def _update_sale_task(self, sale):
        data = {
            'id': sale.pk,
            'date_start': sale.date.start,
            'date_end': sale.date.end,
            'is_active': sale.is_active,
        }
        
        r = requests.post('http://scheduler:8010/sales', data=data)



class AdminSalesImageViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = SaleImageSerializer
    queryset = SaleImage.objects.all()
