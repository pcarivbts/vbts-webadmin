"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.contrib.auth.views import login as contrib_login
from django.shortcuts import redirect
from django.conf import settings

from vbts_webadmin.forms import LoginForm


def login(request, **kwargs):
    """ Dashboard login """
    template_name = 'accounts/login.html'
    redirect_field_name = None
    form = LoginForm
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        return contrib_login(request, template_name, redirect_field_name,
                             form)
