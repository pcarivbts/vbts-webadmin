"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""


from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import ModelForm
from django.forms import Textarea
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Service, ServiceMessages
from vbts_webadmin.tasks import send_sms


class MessageForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('message_send', 'Send Message'))

    class Meta:
        model = ServiceMessages
        fields = ['message']
        widgets = {
            'message': Textarea(attrs={'rows': 4}),
        }


@login_required
def pushmessages_list(request, template_name='pushmessages/list.html'):
    data = {}
    if 'search' in request.GET:
        pushmessages = Service.objects.filter(script__type='P').filter(
            Q(name__icontains=request.GET['search']) |
            Q(keyword__icontains=request.GET['search']) |
            Q(number__icontains=request.GET['search']))
        data['search'] = True
        alerts.info(request,
                    _("You've searched for: '%s'") % request.GET['search'])
    else:
        pushmessages = Service.objects.filter(script__type='P')

    paginator = Paginator(pushmessages, 15)

    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        pushmessages = paginator.page(page)
    except PageNotAnInteger:
        pushmessages = paginator.page(1)
    except EmptyPage:
        pushmessages = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='pushmessages')
    data['pushmessages'] = pushmessages
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def pushmessage_view(request, pk, template_name='pushmessages/detail.html'):
    service = get_object_or_404(Service, pk=pk)
    pushmessages = ServiceMessages.objects.filter(
        service=service).order_by('-id')
    return render(request, template_name,
                  {'service': service, 'pushmessages': pushmessages})


@login_required
def pushmessage_send(request, pk, template_name='pushmessages/send.html'):
    service = get_object_or_404(Service, pk=pk)
    form = MessageForm(request.POST or None)
    if form.is_valid():
        pushmessage = form.save(commit=False)
        pushmessage.service = service
        pushmessage.sender = request.user.userprofile.contact
        pushmessage.date = timezone.now()
        pushmessage.save()

        for subscriber in service.subscribers.all():
            send_sms.delay(subscriber.callerid,
                           pushmessage.sender.callerid,
                           pushmessage.message)
        alerts.success(request,
                       _("You've successfully sent the message '%(msg)s' to "
                         "%(keyword)s's subscribers.") % ({
                             'msg': pushmessage.message,
                             'keyword': service.keyword}))
    return render(request, template_name, {'service': service, 'form': form})
