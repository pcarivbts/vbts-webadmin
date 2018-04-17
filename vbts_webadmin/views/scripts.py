"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Script


@login_required
def script_list(request, template_name='scripts/list.html'):
    data = {}
    if 'search' in request.GET:
        scripts = Script.objects.filter(
            Q(name__icontains=request.GET['search']) | Q(
                description__icontains=request.GET['search']) | Q(
                author__icontains=request.GET['search']))
        data['search'] = True
        alerts.info(
            request, _("You've searched for: '%s'") %
            request.GET['search'])
    else:
        scripts = Script.objects.all()

    paginator = Paginator(scripts, 15)
    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        scripts = paginator.page(page)
    except PageNotAnInteger:
        scripts = paginator.page(1)
    except EmptyPage:
        scripts = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='scripts')
    data['scripts'] = scripts
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def script_view(request, pk, template_name='scripts/detail.html'):
    script = get_object_or_404(Script, pk=pk)
    return render(request, template_name, {'script': script, 'pk': pk})
