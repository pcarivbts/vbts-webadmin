"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import os
import random
import string

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Submit
from django.conf import settings
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.forms import CharField
from django.forms import ModelForm
from django.forms import Textarea
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Ivr

from django.utils.translation import ugettext as _


class IvrForm(ModelForm):
    # tmp_code = forms.CharField()
    tmp_code = CharField(widget=Textarea, required=False)
    tmp_xml_code = CharField(widget=Textarea, required=False)

    def __init__(self, *args, **kwargs):
        update = kwargs.pop('update', None)
        super(IvrForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('ivrs', kwargs={}),
                'Cancel')
        ))

        if update:
            self.fields['tmp_xml_code'].initial = load_xml_from_file(
                self.instance.xml_code)

    class Meta:
        model = Ivr
        exclude = ['code', 'xml_code']


@login_required
def ivr_list(request, template_name='ivrs/list.html'):
    data = {}
    if 'search' in request.GET:
        ivrs = Ivr.objects.filter(
            Q(name__icontains=request.GET['search']) |
            Q(number__icontains=request.GET['search']) |
            Q(description__icontains=request.GET['search']))
        data['search'] = True
        alerts.info(request,
                    _("You've searched for: '%s'") % request.GET['search'])
    else:
        ivrs = Ivr.objects.all()

    paginator = Paginator(ivrs, 15)
    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        ivrs = paginator.page(page)
    except PageNotAnInteger:
        ivrs = paginator.page(1)
    except EmptyPage:
        ivrs = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='ivrs')
    data['ivrs'] = ivrs
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def ivr_view(request, pk, template_name='ivrs/detail.html'):
    ivr = get_object_or_404(Ivr, pk=pk)
    data = {'ivr': ivr}
    return render(request, template_name, data)


@login_required
def ivr_create(request, template_name='ivrs/form.html'):
    form = IvrForm(request.POST or None)
    if form.is_valid():
        filename = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(10))
        save_codes('%s/ivrs/%s.lua' % (settings.MEDIA_ROOT, filename),
                   '%s/ivrs/%s.xml' % (settings.MEDIA_ROOT, filename),
                   form)
        ivr = form.save()
        ivr.code = '%s/ivrs/%s.lua' % (settings.MEDIA_ROOT, filename)
        ivr.xml_code = '%s/ivrs/%s.xml' % (settings.MEDIA_ROOT, filename)
        ivr.save()
        alerts.success(request,
                       _("You've successfully created IVR '%s.'") % ivr.name)
        return redirect('ivrs')
    return render(request, template_name, {'form': form})


@login_required
def ivr_update(request, pk, template_name='ivrs/form.html'):
    ivr = get_object_or_404(Ivr, pk=pk)
    form = IvrForm(request.POST or None, instance=ivr, update=True)
    if form.is_valid():
        form.save()
        save_codes(ivr.code, ivr.xml_code, form)
        alerts.success(request,
                       _("You've successfully updated IVR '%s.'") % ivr.name)
        return redirect('ivrs')
    return render(request, template_name, {'form': form})


@login_required
def ivr_delete(request, pk, template_name='ivrs/confirm_delete.html'):
    ivr = get_object_or_404(Ivr, pk=pk)
    if request.method == 'POST':
        try:
            os.remove(ivr.code)
            os.remove(ivr.xml_code)
        except OSError:
            pass
        ivr.delete()
        alerts.success(request,
                       _("You've successfully deleted IVR '%s.'") % ivr.name)
        return redirect('ivrs')
    return render(request, template_name, {'ivr': ivr})


def save_codes(code_fname, xml_fname, form):
    with open(code_fname, 'w') as f:
        codefile = File(f)
        codefile.write(form.cleaned_data.get('tmp_code'))
    with open(xml_fname, 'w') as f:
        codefile = File(f)
        codefile.write(form.cleaned_data.get('tmp_xml_code'))


def load_xml_from_file(xml_fname):
    with open(xml_fname, 'r') as f:
        codefile = File(f)
        return codefile.read()
