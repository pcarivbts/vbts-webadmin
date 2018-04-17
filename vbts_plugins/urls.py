"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^pcari-plugins/$', views.plugins_json, name='pcari_plugins_json'),
    url(r'^pcari-plugins/(?P<pk>=[^/]+)/$',
        views.plugins_json, name='pcari_plugins_json'),
    url(r'^pcari-plugins/download/(?P<pk>[^/]+)/$',
        views.plugin_download, name='pcari_plugin_download'),
    url(r'^plugins/',
        views.plugin_list, name='pcari_plugins'),
    url(r'^plugin/upload$',
        views.plugin_upload, name='pcari_plugin_upload'),
    url(r'^plugin/update/(?P<pk>[^/]+)/$',
        views.plugin_update, name='pcari_plugin_update'),
    url(r'^plugin/delete/(?P<pk>[^/]+)/$',
        views.plugin_delete, name='pcari_plugin_delete'),
    url(r'^plugin/view/(?P<pk>[^/]+)/$',
        views.plugin_view, name='pcari_plugin_detail'),
]
