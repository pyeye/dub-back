import itertools
import json

from rest_framework import viewsets, generics, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q

from . import elastic
from .models import ProductInfo, Category, Tags, Manufacturer, SFacet, SFacetValue, NFacet, NFacetValue, ProductImage
from apps.authentication.backends import OAuth2Authentication
from apps.authentication.permissions import IsTokenAuthenticated, IsStaff, IsAdminForDelete
from apps.base.pagination import BasePagination
from .serializers import (
    ProductListSerializer,
    ProductTableListSerializer,
    ProductRetriveSerializer,
    ProductCreateSerializer,
    ProductImagesSerializer,
    CategorySerializer,
    TagsSerializer,
    ManufacturerSerializer,
    SFacetSerializer,
    SFacetValueSerializer,
    NFacetSerializer,
)


class AdminProductViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff)
    pagination_class = BasePagination

    def list(self, request, *args, **kwargs):
        product_status = request.query_params.get('status', 'active')
        queryset = ProductInfo.related_objects.filter(status=product_status)
        search = request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(manufacturer__name__icontains=search) |
                Q(category__name__icontains=search) |
                Q(instances__sku__icontains=search)
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductTableListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ProductTableListSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        if instance.status == 'active':
            elastic.index_product(instance)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None, *args, **kwargs):
        model = get_object_or_404(ProductInfo, pk=pk)
        serializer = ProductRetriveSerializer(model)
        data = json.loads(json.dumps(serializer.data))

        sfacets = []
        tmp_sfacets = data['sfacets']
        tmp_sfacets.sort(key=lambda elem: elem['facet']['pk'])
        groups = itertools.groupby(tmp_sfacets, lambda elem: elem['facet'])

        for facet, values in groups:
            facet['values'] = [value['pk'] for value in values]
            sfacets.append(facet)

        data['sfacets'] = sfacets

        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(ProductInfo, pk=pk)
        serializer = ProductCreateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        if product.status == 'active':
            elastic.index_product(product)
        else:
            elastic.delete_product(product)

        return Response(serializer.data)

    def partial_update(self, request, pk=None, *args, **kwargs):
        pass

    def destroy(self, request, pk=None, *args, **kwargs):
        pass


    @list_route(methods=['POST'])
    def images(self, request):
        serializer = ProductImagesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class AdminProductCategoryViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    pagination_class = BasePagination

    def list(self, request, *args, **kwargs):
        is_active = request.query_params.get('is_active', True) in ['1', 'true', 'True', True]
        queryset = Category.objects.filter(is_active=is_active)
        search = request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(name__icontains=search)
        page_query = request.query_params.get('page', None)
        if page_query is not None:
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

        if serializer.data['is_active']:
            elastic_category = {
                'pk': serializer.data['pk'],
                'slug': serializer.data['slug'],
                'name': serializer.data['name'],
            }
            elastic.update_category(elastic_category)

        return Response(serializer.data)

    @detail_route(methods=['DELETE'])
    def deactivate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        products = ProductInfo.objects.filter(category=instance)
        for product in products:
            product.status = 'archive'
            product.save()

        elastic_category = {'pk': instance.pk, 'slug': instance.slug, 'name': instance.name}
        elastic.delete_category(elastic_category)

        return Response(status=status.HTTP_204_NO_CONTENT)



    @detail_route(methods=['PATCH'])
    def activate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = True
        instance.save()

        return Response(status=status.HTTP_200_OK)


class AdminProductManufacturerViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = ManufacturerSerializer
    queryset = Manufacturer.objects.all()
    pagination_class = BasePagination

    def list(self, request, *args, **kwargs):
        is_active = request.query_params.get('is_active', True) in ['1', 'true', 'True', True]
        queryset = Manufacturer.objects.filter(is_active=is_active)
        search = request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(name__icontains=search)

        page_query = request.query_params.get('page', None)
        if page_query is not None:
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

        if serializer.data['is_active']:
            elastic_data = {
                'pk': serializer.data['pk'],
                'slug': serializer.data['slug'],
                'name': serializer.data['name'],
            }
            elastic.update_manufacturer(elastic_data)

        return Response(serializer.data)

    @detail_route(methods=['DELETE'])
    def deactivate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        products = ProductInfo.objects.filter(manufacturer=instance)
        for product in products:
            product.status = 'archive'
            product.save()

        elastic_data = {'pk': instance.pk, 'slug': instance.slug, 'name': instance.name}
        elastic.delete_manufacturer(elastic_data)

        return Response(status=status.HTTP_204_NO_CONTENT)



    @detail_route(methods=['PATCH'])
    def activate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = True
        instance.save()

        return Response(status=status.HTTP_200_OK)


class AdminProductTagsViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = TagsSerializer
    queryset = Tags.objects.all()
    pagination_class = BasePagination


    def list(self, request, *args, **kwargs):
        is_active = request.query_params.get('is_active', True) in ['1', 'true', 'True', True]
        queryset = Tags.objects.filter(is_active=is_active)
        search = request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(name__icontains=search)

        page_query = request.query_params.get('page', None)
        if page_query is not None:
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

        if serializer.data['is_active']:
            elastic_tag = {'pk': serializer.data['pk'], 'name': serializer.data['name']}
            elastic.update_tag(elastic_tag)

        return Response(serializer.data)


    @detail_route(methods=['DELETE'])
    def deactivate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        products = ProductInfo.objects.filter(tags=instance)
        for product in products:
            product.tags.remove(instance)

        elastic_tag = {'pk': instance.pk, 'name': instance.name}
        elastic.delete_tag(elastic_tag)

        return Response(status=status.HTTP_204_NO_CONTENT)



    @detail_route(methods=['PATCH'])
    def activate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = True
        instance.save()

        return Response(status=status.HTTP_200_OK)


class AdminProductSFacetViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = SFacetSerializer
    queryset = SFacet.objects.all()
    pagination_class = BasePagination


    def list(self, request, *args, **kwargs):
        is_active = request.query_params.get('is_active', True) in ['1', 'true', 'True', True]
        queryset = SFacet.objects.filter(is_active=is_active)
        search = request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(name__icontains=search)

        page_query = request.query_params.get('page', None)
        if page_query is not None:
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

        if serializer.data['is_active']:
            elastic_data = {
                'pk': serializer.data['pk'],
                'slug': serializer.data['slug'],
                'name': serializer.data['name']
            }
            elastic.update_sfacet(elastic_data)

        return Response(serializer.data)


    @detail_route(methods=['DELETE'])
    def deactivate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        products = ProductInfo.objects.filter(sfacets__facet=instance)
        for product in products:
            product.sfacets.remove(*product.sfacets.filter(facet=instance))

        elastic.delete_sfacet(instance.pk)

        return Response(status=status.HTTP_204_NO_CONTENT)


    @detail_route(methods=['PATCH'])
    def activate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = True
        instance.save()

        return Response(status=status.HTTP_200_OK)


    @detail_route(methods=['GET'])
    def values(self, request, *args, **kwargs):
        is_active = request.query_params.get('is_active', True) in ['1', 'true', 'True', True]
        instance = self.get_object()
        values = SFacetValue.objects.filter(facet=instance, is_active=is_active)
        serializer = SFacetValueSerializer(values, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class AdminProductSFacetValueViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = SFacetValueSerializer
    queryset = SFacetValue.objects.all()
    pagination_class = BasePagination


    def list(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='GET')


    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='PATCH')


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if instance.is_active != serializer.initial_data['is_active']:
            raise ValidationError(detail='Операция активации/деактивации не доступна по данному адресу')

        serializer.is_valid(raise_exception=True)
        serializer.save()

        if serializer.data['is_active']:
            elastic_data = {
                'pk': serializer.data['pk'],
                'facet_pk': serializer.data['facet'],
                'name': serializer.data['name']
            }
            elastic.update_sfacet_value(elastic_data)

        return Response(serializer.data)


    @detail_route(methods=['DELETE'])
    def deactivate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        products = ProductInfo.objects.filter(sfacets=instance)
        for product in products:
            product.sfacets.remove(instance)

        elastic_data = {
            'pk': instance.pk,
            'facet': {'pk': instance.facet.pk},
        }
        elastic.delete_sfacet_value(elastic_data)

        return Response(status=status.HTTP_204_NO_CONTENT)



    @detail_route(methods=['PATCH'])
    def activate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = True
        instance.save()

        return Response(status=status.HTTP_200_OK)


class AdminProductNFacetViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = NFacetSerializer
    queryset = NFacet.objects.all()
    pagination_class = BasePagination


    def list(self, request, *args, **kwargs):
        is_active = request.query_params.get('is_active', True) in ['1', 'true', 'True', True]
        queryset = NFacet.objects.filter(is_active=is_active)
        search = request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(name__icontains=search)

        page_query = request.query_params.get('page', None)
        if page_query is not None:
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

        if serializer.data['is_active']:
            elastic_data = {
                'pk': serializer.data['pk'],
                'slug': serializer.data['slug'],
                'name': serializer.data['name']
            }
            elastic.update_nfacet(elastic_data)

        return Response(serializer.data)


    @detail_route(methods=['DELETE'])
    def deactivate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        NFacetValue.objects.filter(facet=instance).delete()
        elastic.delete_nfacet(instance.pk)

        return Response(status=status.HTTP_204_NO_CONTENT)



    @detail_route(methods=['PATCH'])
    def activate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = True
        instance.save()

        return Response(status=status.HTTP_200_OK)



class AdminProductImageViewSet(viewsets.ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated, IsStaff, IsAdminForDelete)
    serializer_class = ProductImagesSerializer
    queryset = ProductImage.objects.all()
