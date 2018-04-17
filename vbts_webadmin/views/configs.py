"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Submit
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.forms import ModelForm
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Config


class ConfigForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ConfigForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('configs', kwargs={}),
                'Cancel')
        ))

    class Meta:
        model = Config
        exclude = ['key', 'description']


@login_required
def config_list(request, template_name='configs/list.html'):
    data = {}
    if 'search' in request.GET:
        configs = Config.objects.filter(
            Q(key__icontains=request.GET['search']) |
            Q(value__icontains=request.GET['search']))
        data['search'] = True
        alerts.info(request,
                    _("You've searched for: '%s'") % request.GET['search'])
    else:
        configs = Config.objects.all()

    paginator = Paginator(configs, 15)
    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        configs = paginator.page(page)
    except PageNotAnInteger:
        configs = paginator.page(1)
    except EmptyPage:
        configs = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='configs')
    data['configs'] = configs
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def config_view(request, pk, template_name='configs/detail.html'):
    config = get_object_or_404(Config, pk=pk)
    data = {'config': config}
    return render(request, template_name, data)


@login_required
def config_create(request, template_name='configs/form.html'):
    form = ConfigForm(request.POST or None)
    if form.is_valid():
        config = form.save(commit=False)
        config.save()
        alerts.success(request,
                       _("You've successfully created config '%s.'") %
                       config.key)
        return config_list(request)
    return render(request, template_name, {'form': form})


@login_required
def config_update(request, pk, template_name='configs/form.html'):
    config = get_object_or_404(Config, pk=pk)
    form = ConfigForm(request.POST or None, instance=config)
    if form.is_valid():
        temp = form.save(commit=False)
        temp.save()
        alerts.success(request,
                       _("You've successfully updated config '%s.'") %
                       config.key)
        return config_list(request)
    data = {
        'form': form,
        'config': config
    }
    return render(request, template_name, data)


@login_required
def config_delete(request, pk, template_name='configs/confirm_delete.html'):
    config = get_object_or_404(Config, pk=pk)
    if request.method == 'POST':
        config.delete()
        alerts.success(request,
                       _("You've successfully deleted config '%s.'") %
                       config.key)
        return config_list(request)
    return render(request, template_name, {'config': config})
