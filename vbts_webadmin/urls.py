"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView

import django.contrib.auth.views

from .autocomplete_light import CircleAutocomplete
from .autocomplete_light import ContactAutocomplete
from .autocomplete_light import SipBuddiesAutocomplete

import vbts_webadmin.views.api
import vbts_webadmin.views.api_groups
import vbts_webadmin.views.apps
import vbts_webadmin.views.dashboard
import vbts_webadmin.views.circles
import vbts_webadmin.views.configs
import vbts_webadmin.views.contacts
import vbts_webadmin.views.contact_batch
import vbts_webadmin.views.documents
import vbts_webadmin.views.groups
import vbts_webadmin.views.group_batch
import vbts_webadmin.views.inforequests
import vbts_webadmin.views.messages
import vbts_webadmin.views.promos
import vbts_webadmin.views.promos_batch
import vbts_webadmin.views.pushmessages
import vbts_webadmin.views.reports
import vbts_webadmin.views.scripts
import vbts_webadmin.views.services
import vbts_webadmin.views.subscribers
import vbts_webadmin.views.ivrs


""" Auth """
urlpatterns = [
    url(r'^$', django.contrib.auth.views.login, {
        'template_name': 'accounts/login.html'}, name="login"),
    url(r'^logout/$', django.contrib.auth.views.logout,
        {'next_page': '/'}, name="logout"),
    url(r'^dashboard/$', vbts_webadmin.views.dashboard.home, name='dashboard'),
]

""" User Profiles """
urlpatterns += [url(r'^dashboard/profile/password/change',
                    vbts_webadmin.views.dashboard.profile_change_password,
                    name='change_password'),
                url(r'^dashboard/profile/update',
                    vbts_webadmin.views.dashboard.profile_update,
                    name='profile_update'),
                url(r'^dashboard/profile/',
                    vbts_webadmin.views.dashboard.profile_view,
                    name='profile'),
                ]

""" Configs """
urlpatterns += [
    url(r'^dashboard/configs/',
        vbts_webadmin.views.configs.config_list, name='configs'),
    # url(r'^dashboard/config/new$',
    #     vbts_webadmin.views.configs.config_create, name='config_new'),
    url(r'^dashboard/config/view/(?P<pk>\d+)$',
        vbts_webadmin.views.configs.config_view, name='config_detail'),
    url(r'^dashboard/config/update/(?P<pk>\d+)$',
        vbts_webadmin.views.configs.config_update, name='config_update'),
    # url(r'^dashboard/config/delete/(?P<pk>\d+)$',
    #     vbts_webadmin.views.configs.config_delete, name='config_delete'),
]

"""Circles """
urlpatterns += [
    url(r'^dashboard/circles/',
        vbts_webadmin.views.circles.circle_list, name='circles'),
    url(r'^dashboard/circle/new$',
        vbts_webadmin.views.circles.circle_create, name='circle_new'),
    url(r'^dashboard/circle/view/(?P<pk>\d+)$',
        vbts_webadmin.views.circles.circle_view, name='circle_detail'),
    url(r'^dashboard/circle/update/(?P<pk>\d+)$',
        vbts_webadmin.views.circles.circle_update, name='circle_update'),
    url(r'^dashboard/circle/delete/(?P<pk>\d+)$',
        vbts_webadmin.views.circles.circle_delete, name='circle_delete'),
    url(r'^dashboard/circle/broadcast$',
        vbts_webadmin.views.circles.circle_broadcast, name='circle_broadcast'),
    url(r'^dashboard/circle/broadcast/(?P<pk>\d+)$',
        vbts_webadmin.views.circles.circle_broadcast, name='circle_broadcast'),

]

"""Groups """
urlpatterns += [url(r'^dashboard/groups/',
                    vbts_webadmin.views.groups.group_list,
                    name='groups'),
                url(r'^dashboard/group/view/(?P<pk>\d+)$',
                    vbts_webadmin.views.groups.group_view,
                    name='group_detail'),
                url(r'^dashboard/group/delete/(?P<pk>\d+)$',
                    vbts_webadmin.views.groups.group_delete,
                    name='group_delete'),
                url(r'^dashboard/group/uploadcsv',
                    vbts_webadmin.views.group_batch.simple_upload,
                    name='group_upload_csv'),
                ]

"""Files """
urlpatterns += [
    url(r'^dashboard/documents/',
        vbts_webadmin.views.documents.document_list, name='documents'),
    url(r'^dashboard/document/new$',
        vbts_webadmin.views.documents.document_create, name='document_new'),
    url(r'^dashboard/document/upload$',
        vbts_webadmin.views.documents.document_upload, name='document_upload'),
    url(r'^dashboard/document/delete/(?P<pk>\d+)$',
        vbts_webadmin.views.documents.document_delete, name='document_delete'),
    url(r'^dashboard/document/view/(?P<pk>\d+)$',
        vbts_webadmin.views.documents.document_view, name='document_detail'),
]

"""Reports """
urlpatterns += [url(r'^dashboard/reports/$',
                    vbts_webadmin.views.reports.report_list,
                    name='reports'),
                url(r'^dashboard/report/new$',
                    vbts_webadmin.views.reports.report_create,
                    name='report_new'),
                url(r'^dashboard/report/view/(?P<pk>\d+)$',
                    vbts_webadmin.views.reports.report_view,
                    name='report_detail'),
                url(r'^dashboard/report/update/(?P<pk>\d+)$',
                    vbts_webadmin.views.reports.report_update,
                    name='report_update'),
                url(r'^dashboard/report/publish/(?P<pk>\d+)$',
                    vbts_webadmin.views.reports.report_publish,
                    name='report_publish'),
                url(r'^dashboard/report/print/$',
                    vbts_webadmin.views.reports.PrintReport.as_view(),
                    name='report_print'),
                url(r'^dashboard/report/print/(?P<pk>\d+)$',
                    vbts_webadmin.views.reports.PrintReport.as_view(),
                    name='report_print'),
                ]

# THIS WON'T WORK WITHOUT "APP PLAYSTORE"
# """Plugins """
# urlpatterns += [
#     url(r'^dashboard/plugins/$', vbts_webadmin.views.plugins.plugin_list, name='plugins'),
#     url(r'^dashboard/plugin/install/(?P<pk>[^/]+)/$', vbts_webadmin.views.plugins.plugin_install,
#            name='plugin_install'),
#     url(r'^dashboard/plugin/uninstall/(?P<pk>[^/]+)/$', vbts_webadmin.views.plugins.plugin_uninstall,
#           name='plugin_uninstall'),
#     url(r'^dashboard/plugin/view/(?P<pk>[^/]+)/$',
#         vbts_webadmin.views.plugins.plugin_view, name='plugin_detail'),
# ]

"""Scripts """
urlpatterns += [
    url(r'^dashboard/scripts/$',
        vbts_webadmin.views.scripts.script_list, name='scripts'),
    url(r'^dashboard/script/view/(?P<pk>[^/]+)/$',
        vbts_webadmin.views.scripts.script_view, name='script_detail'),
]

"""Services """
urlpatterns += [url(r'^dashboard/services/(?P<type>\s+)$',
                    vbts_webadmin.views.services.service_list,
                    name='services'),
                url(r'^dashboard/services/',
                    vbts_webadmin.views.services.service_list,
                    name='services'),
                url(r'^dashboard/service/new$',
                    vbts_webadmin.views.services.service_create,
                    name='service_new'),
                url(r'^dashboard/service/view/(?P<pk>\d+)$',
                    vbts_webadmin.views.services.service_view,
                    name='service_detail'),
                url(r'^dashboard/service/update/(?P<pk>\d+)$',
                    vbts_webadmin.views.services.service_update,
                    name='service_update'),
                url(r'^dashboard/service/properties/(?P<pk>\d+)$',
                    vbts_webadmin.views.services.service_update_script_props,
                    name='service_update_script_props'),
                url(r'^dashboard/service/publish/(?P<pk>\d+)$',
                    vbts_webadmin.views.services.service_publish,
                    name='service_publish'),
                url(r'^dashboard/service/reset/(?P<pk>\d+)$',
                    vbts_webadmin.views.services.service_reset_script_props,
                    name='service_reset'),
                url(r'^dashboard/service/delete/(?P<pk>\d+)$',
                    vbts_webadmin.views.services.service_delete,
                    name='service_delete'),
                ]

"""SMS/Messages """
urlpatterns += [
    url(r'^dashboard/messages/',
        vbts_webadmin.views.messages.message_list, name='messages'),
    url(r'^dashboard/message/send$',
        vbts_webadmin.views.messages.message_send, name='message_send'),
    url(r'^dashboard/message/view/(?P<pk>\d+)$',
        vbts_webadmin.views.messages.message_view, name='message_detail'),
]

"""Contacts """
urlpatterns += [url(r'^dashboard/contacts/',
                    vbts_webadmin.views.contacts.contact_list,
                    name='contacts'),
                url(r'^dashboard/contact/new/$',
                    vbts_webadmin.views.contacts.contact_create,
                    name='contact_new'),
                url(r'^dashboard/contact/view/(?P<pk>\d+)$',
                    vbts_webadmin.views.contacts.contact_view,
                    name='contact_detail'),
                url(r'^dashboard/contact/update/(?P<pk>\d+)$',
                    vbts_webadmin.views.contacts.contact_update,
                    name='contact_update'),
                url(r'^dashboard/contact/delete/(?P<pk>\d+)$',
                    vbts_webadmin.views.contacts.contact_delete,
                    name='contact_delete'),
                url(r'^dashboard/contact/addpromo/$',
                    vbts_webadmin.views.contacts.add_promo,
                    name='contact_add_promo'),
                url(r'^dashboard/contact/addpromo/(?P<pk>\d+)$',
                    vbts_webadmin.views.contacts.add_promo,
                    name='contact_add_promo'),
                url(r'^dashboard/contact/create_profile/(?P<pk>\d+)$',
                    vbts_webadmin.views.contacts.contact_create_profile,
                    name='contact_create_profile'),
                url(r'^dashboard/contact/assign_profile/(?P<pk>\d+)$',
                    vbts_webadmin.views.contacts.contact_assign_profile,
                    name='contact_assign_profile'),
                url(r'^dashboard/contact/uploadcsv',
                    vbts_webadmin.views.contact_batch.simple_upload,
                    name='contact_upload_csv'),
                url(r'^dashboard/contact/verify',
                    vbts_webadmin.views.contact_batch.upload_verify,
                    name='contact_upload_verify'),
                ]

"""Promos """
urlpatterns += [url(r'^dashboard/promos/',
                    vbts_webadmin.views.promos.promo_list,
                    name='promos'),
                url(r'^dashboard/promo/new$',
                    vbts_webadmin.views.promos.promo_create,
                    name='promo_new'),
                url(r'^dashboard/promo/view/(?P<pk>\d+)$',
                    vbts_webadmin.views.promos.promo_view,
                    name='promo_detail'),
                url(r'^dashboard/promo/update/(?P<pk>\d+)$',
                    vbts_webadmin.views.promos.promo_update,
                    name='promo_update'),
                url(r'^dashboard/promo/delete/(?P<pk>\d+)$',
                    vbts_webadmin.views.promos.promo_delete,
                    name='promo_delete'),
                url(r'^dashboard/promo/delete_subscription/(?P<pk>\d+)$',
                    vbts_webadmin.views.promos.promo_delete_subscription,
                    name='promo_delete_subscription'),
                url(r'^dashboard/promo/view_subscriptions$',
                    vbts_webadmin.views.promos.promo_view_subscriptions,
                    name='promo_view_subscriptions'),
                url(r'^dashboard/promo/uploadcsv',
                    vbts_webadmin.views.promos_batch.simple_upload,
                    name='promo_upload_csv'),
                ]

"""Sip Buddies """
urlpatterns += [
    url(r'^dashboard/subscribers/',
        vbts_webadmin.views.subscribers.subscribers_list, name='subscribers'),
]

"""APIs """
urlpatterns += [
    url(r'^api/contact/create$', vbts_webadmin.views.api.CreateContact.as_view()),

    url(r'^api/group/create$', vbts_webadmin.views.api_groups.CreateGroup.as_view()),
    url(r'^api/group/delete$', vbts_webadmin.views.api_groups.DeleteGroup.as_view()),
    url(r'^api/group/send$', vbts_webadmin.views.api_groups.SendGroupMsg.as_view()),
    url(r'^api/group/edit$', vbts_webadmin.views.api_groups.EditGroupMems.as_view()),

    url(r'^api/report/submit$', vbts_webadmin.views.api.SubmitReport.as_view()),

    url(r'^api/service/subscribe$',
        vbts_webadmin.views.api.SubscribeToService.as_view()),
    url(r'^api/service/unsubscribe$',
        vbts_webadmin.views.api.UnsubscribeToService.as_view()),
    url(r'^api/service/send$', vbts_webadmin.views.api.SendSubscribersMsg.as_view()),
    url(r'^api/service/status$', vbts_webadmin.views.api.GetServiceStatus.as_view()),
    url(r'^api/service/price', vbts_webadmin.views.api.GetLocalServicePrice.as_view()),
    url(r'^api/service/event', vbts_webadmin.views.api.CreateServiceEvent.as_view()),
    url(r'^api/service/', vbts_webadmin.views.apps.service_details),

    url(r'^api/promo/subscribe$', vbts_webadmin.views.api.PromoSubscribe.as_view()),
    url(r'^api/promo/unsubscribe$',
        vbts_webadmin.views.api.PromoUnsubscribe.as_view()),
    url(r'^api/promo/getservicetype$',
        vbts_webadmin.views.api.GetServiceType.as_view()),
    url(r'^api/promo/getminbal$',
        vbts_webadmin.views.api.GetRequiredBalance.as_view()),
    url(r'^api/promo/getservicetariff',
        vbts_webadmin.views.api.GetServiceTariff.as_view()),
    url(r'^api/promo/getsecavail', vbts_webadmin.views.api.GetSecAvail.as_view()),
    url(r'^api/promo/deduct', vbts_webadmin.views.api.QuotaDeduct.as_view()),
    url(r'^api/promo/status', vbts_webadmin.views.api.GetPromoStatus.as_view()),
    url(r'^api/promo/info', vbts_webadmin.views.api.GetPromoInfo.as_view()),
]


""" IVRs """
urlpatterns += [
    url(r'^dashboard/ivrs/',
        vbts_webadmin.views.ivrs.ivr_list, name='ivrs'),
    url(r'^dashboard/ivr/new$',
        vbts_webadmin.views.ivrs.ivr_create, name='ivr_new'),
    url(r'^dashboard/ivr/view/(?P<pk>\d+)$',
        vbts_webadmin.views.ivrs.ivr_view, name='ivr_detail'),
    url(r'^dashboard/ivr/update/(?P<pk>\d+)$',
        vbts_webadmin.views.ivrs.ivr_update, name='ivr_update'),
    url(r'^dashboard/ivr/delete/(?P<pk>\d+)$',
        vbts_webadmin.views.ivrs.ivr_delete, name='ivr_delete'),
]

"""Others """
urlpatterns += [
    url(r'^contact-us$', TemplateView.as_view(template_name='contact-us.html'),
        name="contact-us"),
    url(r'^pcari-vbts$', TemplateView.as_view(template_name='pcari-vbts.html'),
        name="pcari-vbts"),
    url(r'^contact-autocomplete/$', ContactAutocomplete.as_view(),
        name='contact-autocomplete'),
    url(r'^circle-autocomplete/$', CircleAutocomplete.as_view(),
        name='circle-autocomplete'),
    url(r'^sipbuddies-autocomplete/$', SipBuddiesAutocomplete.as_view(),
        name='sipbuddies-autocomplete'),
]
