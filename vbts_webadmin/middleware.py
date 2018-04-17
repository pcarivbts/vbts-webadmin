"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import pytz
from django.utils import timezone
from django.utils import translation

from vbts_webadmin.models import UserProfile, Config


class TimezoneMiddleware(object):
    """
        Simple middleware for timezone settings
    """

    def process_request(self, request):
        try:
            tzname = UserProfile.objects.get(user=request.user.id).timezone
        except UserProfile.DoesNotExist:
            tzname = 'Asia/Manila'

        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()


class LocaleMiddleware(object):
    """
        Simple middleware for setting language translations
    """

    def process_request(self, request):
        try:
            lang = UserProfile.objects.get(user=request.user.id).language
        except UserProfile.DoesNotExist:
            lang = 'en'

        if lang:
            translation.activate(lang)
        else:
            translation.deactivate()
