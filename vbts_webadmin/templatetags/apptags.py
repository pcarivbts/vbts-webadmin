"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django import template
try:
    import simplejson as json
except ImportError:
    import json
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def is_dict(value):
    if isinstance(value, dict):
        return True
    else:
        return False
