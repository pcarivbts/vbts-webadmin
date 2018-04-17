"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""


class SubscribersRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'vbts_subscribers_psql':
            return 'vbts_subscribers_psql'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'vbts_subscribers_psql':
            return 'vbts_subscribers_psql'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'vbts_subscribers_psql' \
                and obj2._meta.app_label == 'vbts_subscribers_psql':
            return True
        elif 'vbts_subscribers_psql' \
                not in [obj1._meta.app_label, obj2._meta.app_label]:
            return True
        return False

    def allow_syncdb(self, db, model):
        if db == 'vbts_subscribers_psql' \
                or model._meta.app_label == "vbts_subscribers_psql":
            return False
        else:
            return True
