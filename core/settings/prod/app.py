from core.settings.base import *


DEBUG = True

ROOT_URLCONF = 'core.urls.app'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://redis:6379/0",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }
#
# REST_FRAMEWORK_EXTENSIONS = {
#     'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 60
# }

FIRST_DAY_OF_WEEK = 1



EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_TLS = True

FILE_UPLOAD_PERMISSIONS = 0o644
