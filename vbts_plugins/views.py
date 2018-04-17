"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import json
import os

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Submit
from django import forms
from django.conf import settings
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from .models import Plugin


# TODO: auth
def plugins_json(request):
    if 'id' in request.GET:
        data = [{}]
        try:
            plugin = Plugin.objects.get(pk=request.GET['id'])
            data = json.dumps({
                'id': str(plugin.id),
                'name': plugin.name,
                'version': plugin.version,
                'author': plugin.author,
                'description': plugin.description,
                'package': plugin.get_filename,
                'status': 'Download Now',
            })
            return HttpResponse(data, content_type='application/json')
        except BaseException:
            return HttpResponse(data, content_type='application/json')

    if 'search' in request.GET:
        plugins = Plugin.objects.filter(
            Q(name__icontains=request.GET['search']) | Q(
                description__icontains=request.GET['search']))
    else:
        plugins = Plugin.objects.all()

    data = json.dumps([{
        'id': str(p.id),
        'name': p.name,
        'version': p.version,
        'author': p.author,
        'description': p.description,
        'package': p.get_filename,
        'status': 'Download Now',
    } for p in plugins])

    return HttpResponse(data, content_type='application/json')


# TODO: auth
def plugin_download(request, pk):
    plugin = get_object_or_404(Plugin, pk=pk)
    filepath = plugin.package.name
    filename = plugin.package.name.split('/')[-1]
    response = HttpResponse(plugin.package.file,
                            content_type='application/gzip')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


class SearchForm(forms.Form):
    search = forms.CharField(max_length=500)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.form_class = 'form-inline'
        self.helper.form_show_labels = False
        self.helper.add_input(Submit('', 'Search', css_class='btn-primary'))


class PluginForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PluginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('pcari_plugins', kwargs={}),
                'Cancel')
        ))

    class Meta:
        model = Plugin
        exclude = []


@login_required
def plugin_list(request, template_name='vbts_plugins/list.html'):
    data = {}
    if 'search' in request.GET and request.GET['search']:
        plugins = Plugin.objects.filter(
            Q(name__icontains=request.GET['search']) |
            Q(author__icontains=request.GET['search']) |
            Q(description__icontains=request.GET['search']))
        data['search'] = True
        alerts.info(request,
                    'You\'ve searched for: "%s"' % request.GET['search'])
    else:
        plugins = Plugin.objects.all()

    paginator = Paginator(plugins, 15)
    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        plugins = paginator.page(page)
    except PageNotAnInteger:
        plugins = paginator.page(1)
    except EmptyPage:
        plugins = paginator.page(paginator.num_pages)

    search_form = SearchForm()
    data['plugins'] = plugins
    data['is_paginated'] = is_paginated
    data['search_form'] = search_form

    return render(request, template_name, data)


@login_required
def plugin_upload(request, pk=None, template_name='vbts_plugins/form.html'):
    if request.method == 'POST':
        form = PluginForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc = Plugin(name=form.cleaned_data.get('name'),
                            package=request.FILES['package'])
            author = form.cleaned_data.get('author')
            version = form.cleaned_data.get('version')
            description = form.cleaned_data.get('description')
            form.save()
            # commenting out for the meantime, as it always appear
            # in client-side menu
            # alerts.success(request, "You've successfully uploaded a plugin")
            return redirect('pcari_plugins')
    else:
        form = PluginForm()
    return render(request, template_name, {'form': form})


@login_required
def plugin_update(request, pk, template_name='vbts_plugins/form.html'):
    plugin = get_object_or_404(Plugin, pk=pk)
    form = PluginForm(request.POST or None, instance=plugin)
    if form.is_valid():
        form.save()
        # commenting out for the meantime, as it always appear
        # in client-side menu
        # alerts.success(request, "You've successfully updated plugin '%s.'"
        #                % plugin.name)
        return plugin_list(request)
    return render(request, template_name, {'form': form})


@login_required
def plugin_view(request, pk, template_name='vbts_plugins/detail.html'):
    plugin = get_object_or_404(Plugin, pk=pk)
    return render(request, template_name, {'plugin': plugin})


@login_required
def plugin_delete(request, pk,
                  template_name='vbts_plugins/confirm_delete.html'):
    plugin = get_object_or_404(Plugin, pk=pk)
    if request.method == 'POST':
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, plugin.package.name))
        except BaseException:
            pass  # if file is manually deleted, just do nothing
        plugin.delete()
        # commenting out for the meantime, as it always appear
        # in client-side menu
        # alerts.success(request, "You've successfully deleted plugin.")
        return redirect('pcari_plugins')
    return render(request, template_name, {'plugin': plugin})
