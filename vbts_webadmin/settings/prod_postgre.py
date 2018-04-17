"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pcari',
        'USER': 'pcari',
        'PASSWORD': 'pcari',
        'HOST': 'localhost',
        'PORT': '',
    },
    'vbts_subscribers': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/var/lib/asterisk/sqlite3dir/sqlite3.db',
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

STATIC_ROOT = 'static'
