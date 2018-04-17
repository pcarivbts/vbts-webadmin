"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.db import models


class Subscribers(models.Model):
    id = models.IntegerField(primary_key=True)
    imsi = models.CharField(max_length=80)
    balance = models.TextField()

    class Meta:
        managed = False
        db_table = 'subscribers'
        verbose_name = 'Subscribers'
        verbose_name_plural = 'Subscribers'
