from datetime import timedelta
from types import SimpleNamespace

from django.db import transaction
from django.utils import timezone
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.exceptions import FatalClientError
from oauth2_provider.settings import oauth2_settings

class DubValidator(OAuth2Validator):

    def validate_bearer_token(self, token, scopes, request):
        """
        When users try to access resources, check that provided token is valid
        """
        if not token:
            return False

        auth_cache = caches['auth']
        key = 'auth:access_token:{token}'.format(token=token)
        cached_auth = auth_cache.get(key)

        if cached_auth:
            request.user = SimpleNamespace()
            request.scopes = ' '.join(cached_auth['scopes'])
            request.access_token = SimpleNamespace()
            request.access_token.cached_auth = cached_auth
            return True
        else:
            try:
                access_token = AccessToken.objects.select_related("application", "user").get(token=token)
                # if there is a token but invalid then look up the token
                if access_token and access_token.is_valid(scopes):
                    request.client = access_token.application
                    request.user = access_token.user
                    request.scopes = ' '.join(access_token.user.scopes)

                    # this is needed by django rest framework
                    cached_auth = {
                        'uid': access_token.user.id,
                        'scopes': access_token.user.scopes,
                        'token': access_token.token,
                    }
                    auth_cache.set(key, cached_auth, oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
                    access_token.cached_auth = cached_auth

                    request.access_token = access_token
                    return True
                return False
            except AccessToken.DoesNotExist:
                # there is no initial token, look up the token
                return False

    @transaction.atomic
    def save_bearer_token(self, token, request, *args, **kwargs):
        """
        Save access and refresh token, If refresh token is issued, remove or
        reuse old refresh token as in rfc:`6`
        @see: https://tools.ietf.org/html/draft-ietf-oauth-v2-31#page-43
        """

        if "scope" not in token:
            raise FatalClientError("Failed to renew access token: missing scope")

        expires = timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)

        if request.grant_type == "client_credentials":
            request.user = None

        # This comes from OAuthLib:
        # https://github.com/idan/oauthlib/blob/1.0.3/oauthlib/oauth2/rfc6749/tokens.py#L267
        # Its value is either a new random code; or if we are reusing
        # refresh tokens, then it is the same value that the request passed in
        # (stored in `request.refresh_token`)
        refresh_token_code = token.get("refresh_token", None)

        if refresh_token_code:
            # an instance of `RefreshToken` that matches the old refresh code.
            # Set on the request in `validate_refresh_token`
            refresh_token_instance = getattr(request, "refresh_token_instance", None)

            # If we are to reuse tokens, and we can: do so
            if not self.rotate_refresh_token(request) and \
                    isinstance(refresh_token_instance, RefreshToken) and \
                    refresh_token_instance.access_token:

                access_token = AccessToken.objects.select_for_update().get(
                    pk=refresh_token_instance.access_token.pk
                )
                auth_cache = caches['auth']
                auth_cache.delete(access_token.token)

                access_token.user = request.user
                access_token.scope = ' '.join(request.user.scopes)
                access_token.expires = expires
                access_token.token = token["access_token"]
                access_token.application = request.client
                access_token.save()

                cached_auth = {
                    'uid': access_token.user.id,
                    'scopes': access_token.user.scopes,
                    'token': access_token.token,
                    'reused': 'true',
                }
                auth_cache.set(access_token.token, cached_auth, oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)

            # else create fresh with access & refresh tokens
            else:
                # revoke existing tokens if possible to allow reuse of grant
                if isinstance(refresh_token_instance, RefreshToken):
                    try:
                        auth_cache = caches['auth']
                        refresh_token_key = 'auth:access_token:{access_token}:refresh_token'.format(access_token=refresh_token_instance.access_token.token)
                        access_token_key = 'auth:access_token:{access_token}'.format(access_token=refresh_token_instance.access_token.token)
                        auth_cache.delete_many([access_token_key, refresh_token_key])
                        refresh_token_instance.revoke()
                    except (AccessToken.DoesNotExist, RefreshToken.DoesNotExist):
                        pass
                    else:
                        setattr(request, "refresh_token_instance", None)

                # If the refresh token has already been used to create an
                # access token (ie it's within the grace period), return that
                # access token
                # TODO rewrite to celery
                access_token = self._create_access_token(
                    expires,
                    request,
                    token,
                )

                refresh_token = RefreshToken(
                    user=request.user,
                    token=refresh_token_code,
                    application=request.client,
                    access_token=access_token
                )
                refresh_token.save()

                auth_cache = caches['auth']
                key = 'auth:access_token:{access_token}:refresh_token'.format(access_token=access_token.token)
                auth_cache.set(key, access_token.token, oauth2_settings.REFRESH_TOKEN_EXPIRE_SECONDS)

        # No refresh token should be created, just access token
        else:
            self._create_access_token(expires, request, token)

        # TODO: check out a more reliable way to communicate expire time to oauthlib
        token["expires_in"] = oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS

    def _create_access_token(self, expires, request, token, source_refresh_token=None):
        access_token = AccessToken(
            user=request.user,
            scope=' '.join(request.user.scopes),
            expires=expires,
            token=token["access_token"],
            application=request.client,
        )
        access_token.save()

        auth_cache = caches['auth']
        cached_auth = {
            'uid': access_token.user.id,
            'scopes': access_token.user.scopes,
            'token': access_token.token,
        }
        key = 'auth:access_token:{token}'.format(token=access_token.token)
        auth_cache.set(key, cached_auth, oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)

        return access_token

    def revoke_token(self, token, token_type_hint, request, *args, **kwargs):
        """
        Revoke an access or refresh token.
        :param token: The token string.
        :param token_type_hint: access_token or refresh_token.
        :param request: The HTTP Request (oauthlib.common.Request)
        """
        if token_type_hint not in ["access_token", "refresh_token"]:
            token_type_hint = None

        token_types = {
            "access_token": AccessToken,
            "refresh_token": RefreshToken,
        }

        token_type = token_types.get(token_type_hint, AccessToken)
        try:
            token_type.objects.get(token=token).revoke()
            auth_cache = caches['auth']
            auth_cache.delete(token)
        except ObjectDoesNotExist:
            for other_type in [_t for _t in token_types.values() if _t != token_type]:
                # slightly inefficient on Python2, but the queryset contains only one instance
                list(map(lambda t: t.revoke(), other_type.objects.filter(token=token)))