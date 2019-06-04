from rest_framework.exceptions import ValidationError
from rest_framework import generics, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import caches

from apps.authentication.backends import JWTAuthentication, OAuth2Authentication
from apps.authentication.permissions import IsTokenAuthenticated
from .serializers import CustomerSerializer, CustomerCompanySerializer, CustomerChangePassSerializer, StaffSerializer
from .models import User


class CustomerAPIView(mixins.CreateModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = CustomerCompanySerializer
    permission_classes = (IsTokenAuthenticated,)


    def get_authenticators(self):
        if self.request.method.lower() == 'post':
            authentication = [JWTAuthentication]
        else:
            authentication = [OAuth2Authentication]

        return [auth() for auth in authentication]

    def _get_serializer_class(self, is_company):
        if is_company is None:
            raise ValidationError('is_company Обязательное поле')

        return CustomerCompanySerializer if is_company else CustomerSerializer


    def post(self, request, *args, **kwargs):
        is_company = request.data.get('is_company', None)
        serializer_class = self._get_serializer_class(is_company)
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def patch(self, request, *args, **kwargs):
        is_company = request.data.get('is_company', None)
        queryset = User.objects.get(pk=request.auth.cached_auth['uid'])
        serializer_class = self._get_serializer_class(is_company)
        serializer = serializer_class(queryset, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)


class PasswordAPIView(mixins.CreateModelMixin, generics.GenericAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated,)
    queryset = User.objects.all()
    serializer_class = CustomerChangePassSerializer

    def post(self, request, *args, **kwargs):
        user = User.objects.get(pk=request.auth.cached_auth['uid'])
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)


class BaseSessionAPIView(APIView):
    authentication_classes = [JWTAuthentication, OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated,)
    _history_type = None
    session_expire_seconds = 432000

    def get(self, request):
        key = 'history:{history_type}:{user}'.format(user=request.auth.cached_auth['uid'],
                                                     history_type=self._history_type)
        cache = caches['history']
        data = cache.get(key)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.get('data', None)
        key = 'history:{history_type}:{user}'.format(user=request.auth.cached_auth['uid'],
                                                     history_type=self._history_type)
        cache = caches['history']
        cache.set(key, data, self.session_expire_seconds)
        return Response(data, status=status.HTTP_201_CREATED)


class CartSessionAPIView(BaseSessionAPIView):
    _history_type = 'cart'


class WatchedSessionAPIView(BaseSessionAPIView):
    _history_type = 'watched'
