import datetime

from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from apps.base.pagination import BasePagination
from .serializers import SaleApiSerializer
from .models import Sale


class SalesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SaleApiSerializer
    pagination_class = BasePagination

    def get_queryset(self):
        today = datetime.datetime.today()
        queryset = Sale.objects.filter(is_active=True, date_start__lte=today, date_end__gte=today)
        return queryset
