"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import absolute_import

import csv
import io

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.conf import settings
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from django.utils.translation import ugettext as _

from vbts_webadmin.models import Contact
from vbts_webadmin.models import Document
from vbts_webadmin.models import Group
from vbts_webadmin.models import GroupMembers
from vbts_webadmin.views import api_groups


class DocumentForm(forms.ModelForm):
    ACTION_CHOICES = [
        (1, 'Create'),
        # (2, 'Delete'),
    ]

    OBJ_CHOICES = [
        (1, 'Groups'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    object = forms.ChoiceField(choices=OBJ_CHOICES)

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'

        self.helper.layout = Layout(
            Fieldset(_("What do you want to do?"),
                     'action',
                     'object'
                     ),
            Fieldset(_("Upload your CSV file containing data"),
                     'docfile'
                     ),
            Submit('save', 'Save'),
            HTML(
                '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                    reverse_lazy('groups', kwargs={}), 'Cancel')
            )
        )

    def clean_docfile(self):
        allowed_content_types = ['text/csv']
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
            raise forms.ValidationError(_(
                'File type is not supported. Only CSV files are allowed.'))

        return docfile

    class Meta:
        model = Document
        exclude = ['name', 'description']
        labels = {
            "docfile": "Input file (*.csv)"
        }


@login_required
def simple_upload(request, template_name='groups/upload_csv.html'):
    csv_subs_len = 2
    csv_group_len = 6
    fail = False

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            myfile = request.FILES['docfile']
            actobj = form.cleaned_data.get('action') + \
                form.cleaned_data.get('object')

            reader = csv.reader(io.StringIO(myfile.read().decode('utf-8')))
            headers = next(reader)  # handle row header

            failed = []
            invalid = []
            if actobj == '11':  # Create groups
                if len(headers) < csv_group_len:
                    fail = True
                    alerts.warning(request, _(
                        "Missing required fields. Check your CSV file again."
                    ))

                for row in reader:
                    if len(row) < csv_group_len:
                        break  # do nothing
                    try:
                        owner = Contact.objects.get(callerid=row[0])
                        (new_group, created) = Group.objects.update_or_create(
                            name='GD-%s' % owner.imsi,
                            defaults={
                                'owner': owner,
                                'name': 'GD-%s' % owner.imsi,
                                'last_modified': timezone.now()
                            }
                        )

                        GroupMembers.objects.filter(group=new_group).delete()

                        mems = []
                        for i in range(1, 6):
                            if row[i]:
                                mems.append(row[i])

                        invalid = api_groups.add_group_members(mems,
                                                               new_group)
                    except Exception as e:
                        print (e)
                        failed.append(row[0])

            else:
                pass

            myfile.close()
            if fail or failed or invalid:
                alerts.warning(
                    request,
                    _('Errors encountered when trying to add the following: '
                      '%s, %s') % (failed, invalid))
            else:
                alerts.success(
                    request,
                    _("Batch operation completed successfully."))
            return redirect('groups')
    else:
        form = DocumentForm()
    return render(request, template_name, {'form': form})
