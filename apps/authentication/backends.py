"""
Authentication backends for rest framework.
This module exposes four backends.

The first backend uses JSON Web Token, self contained
token that makes authentication more statless.
Example: Authorization: JWT AbHsgf49t.Hto7YegBtr7.94tygO9

Second backend inherited from JSON Web Token authentication
and ignores expr (expiration refresh time) clime.

Third backend used as simple authentication against
user_id and password in POST parameters.

Last backend used as http basic authentication against
user_id and password.

For login user (create token) can be used by the third or fourth
backends or both.
"""

from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.core.cache import caches
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from oauth2_provider.backends import get_oauthlib_core
import jwt

from .exceptions import TokenExpire


class JWTAuthentication(BaseAuthentication):
    """
    Authenticate against an JWT access token for protected resources.
    Return tuple of user and dict of payload decoded JWT,or
    anonymous user and None if Authentication header not exist.
    Raise exception AuthenticationFailed if header exist and
    there was error its verification.
    """

    jwt_secret = settings.SECRET_KEY
    jwt_prefix = "JWT"
    jwt_algorithm = "HS256"

    def authenticate(self, request, **credentials):
        if request.method == "OPTIONS":
            return None

        auth_header = get_authorization_header(request).split()
        if not auth_header or len(auth_header) != 2:
            return None
        token = auth_header[1]
        try:
            payload = jwt.decode(
                jwt=token,
                key=self.jwt_secret,
                algoritms=[self.jwt_algorithm],
                verify=True,
            )
        except jwt.InvalidTokenError:
            return None

        user = AnonymousUser()
        auth = SimpleNamespace()
        auth.cached_auth = payload
        return user, auth

    def authenticate_header(self, request):
        return 'JWT realm="api"'


class OAuth2Authentication(BaseAuthentication):
    """
    OAuth 2 authentication backend using `django-oauth-toolkit`
    """

    www_authenticate_realm = "api"

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """
        if request.method == "OPTIONS":
            return None

        oauthlib_core = get_oauthlib_core()
        valid, r = oauthlib_core.verify_request(request, scopes=[])

        if not valid:
            auth_header = get_authorization_header(request).split()
            if not auth_header or len(auth_header) != 2:
                return None
            token = auth_header[1].decode("utf-8")
            auth_cache = caches["auth"]
            key = f"auth:access_token:{token}:refresh_token"
            cached_refresh_token = auth_cache.get(key)
            if cached_refresh_token:
                raise TokenExpire
            return None

        return r.user, r.access_token

    def authenticate_header(self, request):
        """
        Bearer is the only finalized type currently
        """
        return f"Bearer realm={self.www_authenticate_realm}"
