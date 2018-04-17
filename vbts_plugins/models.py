"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.db import models
import os
import uuid


class Plugin(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=40, blank=False, null=False)
    author = models.CharField(max_length=255, blank=False, null=False)
    version = models.CharField(max_length=10, blank=False, null=False)
    description = models.TextField(blank=True)
    package = models.FileField(upload_to='plugins')
    date_uploaded = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pcari_plugins'
        verbose_name = 'Plugin'
        verbose_name_plural = 'Plugins'

    def __unicode__(self):
        return "%s %s" % (self.name, self.version)

    @property
    def get_filename(self):
        return os.path.basename(self.package.name)

# @receiver(models.signals.post_delete, sender=Plugin)
# def auto_delete_file_on_delete(sender, instance, **kwargs):
#     """Deletes file from filesystem
#     when corresponding `MediaFile` object is deleted.
#     """
#     if instance.package:
#         if os.path.isfile(instance.package.path):
#             os.remove(instance.package.path)
#
# @receiver(models.signals.pre_save, sender=Plugin)
# def auto_delete_file_on_change(sender, instance, **kwargs):
#     """
#     Deletes file from filesystem
#     when corresponding `Plugin` object is changed.
#     """
#     if not instance.pk:
#         return False
#
#     try:
#         old_file = Plugin.objects.get(pk=instance.pk).package
#     except Plugin.DoesNotExist:
#         return False
#
#     new_file = instance.package
#     if not old_file == new_file:
#         if os.path.isfile(old_file.path):
#             os.remove(old_file.path)
