"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import os
from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = bool(os.environ.get('DEBUG', False) == "True")

FORCE_SCRIPT_NAME = ""

ALLOWED_HOSTS = ['*']

SECRET_KEY = os.environ["SECRET_KEY"]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'dal',
    'dal_select2',
    'crispy_forms',
    'easy_pdf',
    'mathfilters',
    'djcelery',
    'vbts_plugins',
    'vbts_subscribers',
    'vbts_webadmin',
]

AUTH_PROFILE_MODULE = 'vbts_webadmin.UserProfile'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'vbts_webadmin.middleware.TimezoneMiddleware',
    'vbts_webadmin.middleware.LocaleMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'templates/public'),
        ],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'debug': True,
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'databases/pcari3.db'),
    },
    'vbts_subscribers': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'databases/sqlite3.db'),
        # 'NAME': '/var/lib/asterisk/sqlite3dir/sqlite3.db',
    },
    'vbts_subscribers_psql': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'endaga',
        'USER': 'endaga',
        'PASSWORD': 'endaga',
        'HOST': 'localhost',
        'PORT': '',
    }
}

DATABASE_ROUTERS = [
    'vbts_subscribers.routers.SubscribersRouter',
    'vbts_subscribers_psql.routers.SubscribersRouter',
]

WSGI_APPLICATION = 'vbts_webadmin.wsgi.application'

LANGUAGES = [
    ('en', _('English')),
    ('tl', _('Tagalog')),
]

LANGUAGE_CODE = 'en-us'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]
TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = ''
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

FIXTURE_DIRS = (
    'fixtures',
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

LOGIN_URL = '/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/dashboard/'

CRISPY_TEMPLATE_PACK = 'bootstrap3'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

TWITTER = {
    'CONSUMER_KEY': os.environ['TWITTER_CONSUMER_KEY'],
    'CONSUMER_SECRET': os.environ['TWITTER_CONSUMER_SECRET'],
    'TOKEN': os.environ['TWITTER_TOKEN'],
    'TOKEN_SECRET': os.environ['TWITTER_TOKEN_SECRET']
}

CHATPLAN_DIR = "/etc/freeswitch/chatplan/default/"
DIALPLAN_DIR = "/etc/freeswitch/dialplan/default/"

PCARI = {
    'ADMIN_CALLERID': '0000',
    'ADMIN_IMSI': 'IMSI0000000000',
    'CLOUD_URL': 'http://192.168.60.100:7000/server/',
    'PLUGINS_DOWNLOAD_URL': 'http://192.168.60.100:7000/server/pcari-plugins/download/',
    'DOWNLOADS_DIR': os.path.join(
        MEDIA_ROOT,
        'downloads'),
    'CHATPLAN_TEMPLATES_DIR': os.path.join(
        MEDIA_ROOT,
        'templates/chatplans')}

CELERY_TIMEZONE = 'UTC'
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

MAX_UPLOAD_SIZE = 10485760  # 10MB

BROKER_URL = os.environ["BROKER_URL"]
