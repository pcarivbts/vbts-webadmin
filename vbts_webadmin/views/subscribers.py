"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render
from django.utils.translation import ugettext as _

from vbts_subscribers.models import SipBuddies
from vbts_webadmin.forms import SearchForm


@login_required
def subscribers_list(request, template_name='subscribers/list.html'):
    data = {}
    if 'search' in request.GET:
        subscribers = SipBuddies.objects.all()
        for term in request.GET['search'].split():
            subscribers = subscribers.filter(Q(name__icontains=term) |
                                             Q(callerid__icontains=term))

        data['search'] = True
        alerts.info(request,
                    _("You've searched for: '%s'") % request.GET['search'])
    else:
        subscribers = SipBuddies.objects.all()

    paginator = Paginator(subscribers, 15)
    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        subscribers = paginator.page(page)
    except PageNotAnInteger:
        subscribers = paginator.page(1)
    except EmptyPage:
        subscribers = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='subscribers')
    data['subscribers'] = subscribers
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)
