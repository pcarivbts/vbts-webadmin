"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import os

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Submit
from dal import autocomplete
from django.conf import settings
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.forms import ModelForm, Textarea, ValidationError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template import Template, Context
from django.utils import timezone
from django.utils.translation import ugettext as _
from easy_pdf.views import PDFTemplateView

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Report
from vbts_webadmin.models import ReportManagers
from vbts_webadmin.models import ReportMessages
from vbts_webadmin.tasks import reload_fs_xml


class ReportForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('reports', kwargs={}),
                'Cancel')
        ))

    #     def clean(self):
    #         if self.instance.pk is not None:
    #             if (self.instance.keyword != self.cleaned_data['keyword']
    #                 or self.instance.number != self.cleaned_data['number']):

    def clean_keyword(self):
        return self.cleaned_data['keyword'].upper()

    def clean_status(self):
        if not self.cleaned_data['status']:
            raise ValidationError(_('This field is required.'))
        else:
            return self.cleaned_data['status']

    class Meta:
        model = Report
        exclude = [
            'author',
            'chatplan',
            'status',
            'created_date',
            'published_date']
        widgets = {
            'managers': autocomplete.ModelSelect2Multiple(
                url='contact-autocomplete',
                attrs={'rows': 2}),
            'description':
                Textarea(attrs={'class': 'textinput-message', 'rows': 2})
        }


@login_required
def report_list(request, template_name='reports/list.html'):
    data = {}
    if 'search' in request.GET:
        reports = Report.objects.filter(
            Q(name__icontains=request.GET['search']) |
            Q(keyword__icontains=request.GET['search']) |
            Q(number__icontains=request.GET['search']))
        data['search'] = True
        alerts.info(request,
                    _("You've searched for: '%s'") % request.GET['search'])
    else:
        reports = Report.objects.all()

    paginator = Paginator(reports, 15)
    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='reports')
    data['reports'] = reports
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def report_create(request, template_name='reports/form.html'):
    form = ReportForm(request.POST or None)
    if form.is_valid():
        report = form.save(commit=False)
        report.author = request.user
        report.created_date = timezone.now()
        report.save()
        report.managers.clear()
        for manager in form.cleaned_data.get('managers'):
            report_manager = ReportManagers.objects.create(
                manager=manager, report=report)
            report_manager.save()

        alerts.success(
            request,
            _("You've successfully created '%s' report.") %
            report.keyword)
        return redirect('reports')
    return render(request, template_name, {'form': form})


@login_required
def report_update(request, pk, template_name='reports/form.html'):
    report = get_object_or_404(Report, pk=pk)
    form = ReportForm(request.POST or None, instance=report)
    if form.is_valid():
        report = form.save(commit=False)
        report.save()
        report.managers.clear()
        for manager in form.cleaned_data.get('managers'):
            report_manager = ReportManagers.objects.create(
                manager=manager, report=report)
            report_manager.save()
        alerts.success(
            request,
            _("You've successfully updated '%s' report.") %
            report.keyword)
        return redirect('reports')
    return render(request, template_name, {'form': form})


@login_required
def report_view(request, pk, template_name='reports/detail.html'):
    report = get_object_or_404(Report, pk=pk)
    reports = ReportMessages.objects.filter(report=report).order_by('-date')
    return render(request, template_name,
                  {'report': report, 'reports': reports})


@login_required
def report_publish(request, pk, template_name='reports/publish.html'):
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST' and 'status' in request.POST:
        report.status = request.POST.get("status")
        report.save()
        if report.status == "P":
            status = "published"
            create_or_update_chatplan(report)
        else:
            status = "unpublished"
            delete_chatplan(report)
        message = _("You've successfully %(status)s '%(report)s' report.") % ({
            'status': status,
            'report': report})
        alerts.success(request, message)
        return redirect('reports')
    return render(request, template_name, {'report': report})


def create_or_update_chatplan(instance):
    if instance.chatplan:
        try:
            old_chatplan = os.path.join(settings.CHATPLAN_DIR,
                                        instance.chatplan)
            os.remove(old_chatplan)
        except OSError:
            pass

    template = os.path.join(settings.PCARI['CHATPLAN_TEMPLATES_DIR'],
                            "report.xml")
    fp = open(template)
    t = Template(fp.read())
    fp.close()
    xml = t.render(
        Context({'keyword': instance.keyword, 'number': instance.number}))

    instance.chatplan = '17_REPORT_%s.xml' % instance.keyword
    chatplan_path = os.path.join(settings.CHATPLAN_DIR,
                                 instance.chatplan)

    f = open(chatplan_path, 'w')
    myfile = File(f)
    myfile.write(xml)
    myfile.close()
    instance.chatplan = chatplan_path
    instance.save()


def delete_chatplan(instance):
    try:
        if instance.chatplan:
            chatplan_path = os.path.join(settings.CHATPLAN_DIR,
                                         instance.chatplan)
            os.remove(chatplan_path)
            reload_fs_xml.delay()
    except OSError:
        pass


class PrintReport(PDFTemplateView):
    template_name = "reports/print.html"

    def get_context_data(self, **kwargs):
        if 'pk' in self.kwargs:
            pk = self.kwargs['pk']
            self.template_name = "reports/print.html"
            report = get_object_or_404(Report, pk=pk)
            reports = ReportMessages.objects.filter(
                report=report).order_by('-date')
        else:
            self.template_name = "reports/print_all.html"
            report = {}
            reports = ReportMessages.objects.all().order_by('-date')

        return super(PrintReport, self).get_context_data(
            pagesize="A4",
            report=report,
            reports=reports,
            **kwargs
        )
