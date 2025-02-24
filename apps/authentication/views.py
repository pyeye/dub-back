import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import jwt

from .backends import JWTAuthentication, OAuth2Authentication
from .permissions import IsTokenAuthenticated
from apps.users.models import User, Staff
from apps.users.serializers import CustomerSerializer, StaffSerializer


class CreateGuestView(APIView):

    def post(self, request):
        jwt_secret = settings.SECRET_KEY
        guest_id = 'guest_{id}'.format(id=str(uuid.uuid4())[:8])
        payload = {
            'uid': guest_id,
            'scopes': ['guest'],
        }
        token = jwt.encode(payload, jwt_secret).decode('utf-8')
        return Response(data=token, status=status.HTTP_201_CREATED)


class JWTUserView(APIView):

    authentication_classes = [OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated,)

    def get(self, request):
        queryset = Staff.objects.get(user__pk=request.auth.cached_auth['uid'])
        serializer = StaffSerializer(queryset)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class SecretView(APIView):

    authentication_classes = [JWTAuthentication, OAuth2Authentication]
    permission_classes = (IsTokenAuthenticated,)

    def get(self, request):
        return Response(data=request.auth.cached_auth, status=status.HTTP_200_OK)


