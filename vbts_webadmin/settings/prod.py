"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'databases/pcari.db'),
    },
    'vbts_subscribers': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/var/lib/asterisk/sqlite3dir/sqlite3.db',
    }
}

STATIC_ROOT = 'static'
