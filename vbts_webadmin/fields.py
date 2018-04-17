"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.db import models
from .widgets import MultiValuesWidget


class MultiValuesFormField(forms.Field):
    message = _('Enter values separated by commas.')
    code = 'invalid'
    widget = MultiValuesWidget

    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return None if no input was given.
        if not value:
            return []
        return [v.strip() for v in value.splitlines() if v != ""]


class MultiValuesField(models.Field):
    description = "A multi values field stored as a multi-lines text"

    __metaclass__ = models.SubfieldBase

    def formfield(self, **kwargs):
        defaults = {'form_class': MultiValuesFormField}
        defaults.update(kwargs)
        return super(MultiValuesField, self).formfield(**defaults)

    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, str):
            return value
        elif isinstance(value, list):
            return "\n".join(value)

    def to_python(self, value):
        if not value:
            return []
        if isinstance(value, list):
            return value
        return value.splitlines()

    def get_internal_type(self):
        return 'TextField'


try:
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], ["fields.MultiValuesField"])
except ImportError:
    pass
