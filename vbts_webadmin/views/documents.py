"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import os

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout
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
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Document
from vbts_webadmin.widgets import AceWidget


class DocumentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('documents', kwargs={}),
                'Cancel')
        ))

    def clean_docfile(self):

        allowed_content_types = ['text/plain', 'text/csv', 'application/json']
        settings.MAX_UPLOAD_SIZE

        docfile = self.cleaned_data['docfile']
        docfile_type = docfile.content_type

        if docfile_type in allowed_content_types:
            if docfile._size > settings.MAX_UPLOAD_SIZE:
                raise forms.ValidationError(
                    _('Please keep filesize under %s. Current filesize %s.') %
                    (filesizeformat(
                        settings.MAX_UPLOAD_SIZE), filesizeformat(
                        docfile._size)))
        else:
            raise forms.ValidationError(
                _('File type is not supported. Allowed types are: csv, json, and text files.'))
        return docfile

    class Meta:
        model = Document
        exclude = []
        labels = {
            "docfile": "Document (.csv, .json, .txt)"
        }


class DocumentEditorForm(forms.ModelForm):
    content = forms.CharField(widget=AceWidget(wordwrap=False,
                                               mode='javascript',
                                               theme='clouds',
                                               width="900px",
                                               height="400px"))

    def __init__(self, *args, **kwargs):
        super(DocumentEditorForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        # self.helper.form_class = 'form-horizontal'  # adjust first widget size
        # self.helper.label_class = 'col-lg-2'
        # self.helper.field_class = 'col-lg-8'
        self.helper.form_method = 'post'
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.helper.layout = Layout('content')
            self.helper.layout.append(Submit('submit', 'Update'))
        else:
            self.helper.layout = Layout('name', 'description', 'content')
            self.helper.layout.append(Submit('submit', 'Save'))
            self.helper.layout.append(
                HTML('<a class="btn btn-default" href="{}">{}</a>'.format(
                    reverse_lazy('documents', kwargs={}),
                    'Cancel')
                )
            )

    def save(self, commit=True):
        document = super(DocumentEditorForm, self).save(commit=False)
        name = self.cleaned_data['name'].replace(' ', '_')
        document.docfile = 'documents/%s' % name

        document.save()
        filepath = os.path.join(settings.MEDIA_ROOT, 'documents/%s' % name)
        f = open(filepath, 'w+b')
        f.write(self.cleaned_data['content'])

    class Meta:
        model = Document
        exclude = ['docfile']


@login_required
def document_list(request, template_name='documents/list.html'):
    data = {}
    if 'search' in request.GET:
        documents = Document.objects.filter(
            Q(docfile__icontains=request.GET['search']))
        data['search'] = True
        alerts.info(request,
                    _('You\'ve searched for: "%s"') % request.GET['search'])
    else:
        documents = Document.objects.all()

    paginator = Paginator(documents, 15)
    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        documents = paginator.page(page)
    except PageNotAnInteger:
        documents = paginator.page(1)
    except EmptyPage:
        documents = paginator.page(paginator.num_pages)

    search_form = SearchForm(form_action='documents')
    data['documents'] = documents
    data['is_paginated'] = is_paginated
    data['search_form'] = search_form

    return render(request, template_name, data)


@login_required
def document_create(request, template_name='documents/form.html'):
    form = DocumentEditorForm(request.POST or None)
    if form.is_valid():
        form.save()
        alerts.success(request, _("You've successfully created the document."))
        return redirect('documents')
    return render(request, template_name, {'form': form})


@login_required
def document_upload(request, template_name='documents/form.html'):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc = Document(name=form.cleaned_data.get('name'),
                              docfile=request.FILES['docfile'],
                              description=form.cleaned_data.get('description'))
            newdoc.save()
            alerts.success(request, _(
                "You've successfully uploaded a document"))
            return redirect('documents')
    else:
        form = DocumentForm()
    return render(request, template_name, {'form': form})


@login_required
def document_view(request, pk, template_name='documents/detail.html'):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST' and request.POST['content']:
        f = open(document.docfile.path, 'w+b')
        content = request.POST['content']
        f.write(content)
        alerts.success(request, _("You've successfully updated the document."))
        return redirect('documents')
    data = {'content': document.docfile.read()}
    form = DocumentEditorForm(initial=data)
    return render(request, template_name, {'document': document, 'form': form})


def document_delete(
        request,
        pk,
        template_name='documents/confirm_delete.html'):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, document.docfile.name))
        except BaseException:
            pass  # if file is manually deleted, just do nothing
        document.delete()
        alerts.success(request, _("You've successfully deleted document."))
        return redirect('documents')
    return render(request, template_name, {'document': document})
