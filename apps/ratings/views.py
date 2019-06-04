from django.db.models import Case, When, BooleanField
from rest_framework import viewsets, generics, mixins, status
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from rest_framework.response import Response

from .serializers import CustomerRatingListSerializer, CustomerRatingSerializer
from .models import CustomerRating

from apps.authentication.backends import OAuth2Authentication
from apps.authentication.permissions import IsTokenAuthenticated


class RatingListAPIView(mixins.ListModelMixin, generics.GenericAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated,)
    serializer_class = CustomerRatingListSerializer
    queryset = CustomerRating.objects.all()

    def get(self, request, *args, **kwargs):
        instance = CustomerRating.objects.filter(customer__pk=request.auth.cached_auth['uid']).annotate(is_edited=Case(
            When(rating=0.0, then=True),
            default=False,
            output_field=BooleanField()
        )).order_by('-is_edited', 'product__name')
        serializer = CustomerRatingListSerializer(instance, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class RatingUpdateAPIView(mixins.UpdateModelMixin, generics.GenericAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated,)
    serializer_class = CustomerRatingSerializer
    queryset = CustomerRating.objects.all()

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class RatingCustomerAPIView(mixins.ListModelMixin, generics.GenericAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated,)
    serializer_class = CustomerRatingSerializer
    queryset = CustomerRating.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = CustomerRating.objects.filter(customer__pk=request.auth.cached_auth['uid'])
        category = self.request.query_params.get('category', None)
        if category is not None:
            queryset = queryset.filter(product__category__code=category)
        serializer = CustomerRatingSerializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)