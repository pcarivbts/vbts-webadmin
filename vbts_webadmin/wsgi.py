"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.

-

WSGI config for vbts_webadmin project.
For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/

"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vbts_webadmin.settings.prod")

application = get_wsgi_application()
