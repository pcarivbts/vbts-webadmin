"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""


class SubscribersRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'vbts_subscribers':
            return 'vbts_subscribers'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'vbts_subscribers':
            return 'vbts_subscribers'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'vbts_subscribers' \
                and obj2._meta.app_label == 'vbts_subscribers':
            return True
        elif 'vbts_subscribers' \
                not in [obj1._meta.app_label, obj2._meta.app_label]:
            return True
        return False

    def allow_syncdb(self, db, model):
        if db == 'vbts_subscribers' \
                or model._meta.app_label == "vbts_subscribers":
            return False
        else:
            return True
