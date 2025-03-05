from core.settings.base import *


DEBUG = True

INSTALLED_APPS += [
    'debug_toolbar',
]

ROOT_URLCONF = 'core.urls'

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}

DEBUG_TOOLBAR_PATCH_SETTINGS = False
INTERNAL_IPS = ['0.0.0.0', '127.0.0.1']
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar,
}

ELASTIC_SEARCH = {
    'INDEX': 'products_dev',
    'PAGE_SIZE': 24,
    'CONFIG': {
        'host': 'elastic',
        'port': 9200,
        'http_auth': ('elastic', 'secret')
    },
}


