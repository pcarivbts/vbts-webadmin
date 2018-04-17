"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import absolute_import

from datetime import timedelta

import os
import glob
from celery import Celery
from django.conf import settings

env_dir = 'envdir'
env_vars = glob.glob(os.path.join(env_dir, '*'))
for env_var in env_vars:
    with open(env_var, 'r') as env_var_file:
        os.environ.setdefault(env_var.split(os.sep)[-1],
                              env_var_file.read().strip())

app = Celery('vbts_webdadmin')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
