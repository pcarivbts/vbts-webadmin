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
from vbts_webadmin.models import ContactProfile
from vbts_webadmin.models import ContactSimcards
from vbts_webadmin.models import Document
from vbts_webadmin.models import Group
from vbts_webadmin.views import api_groups


class DocumentForm(forms.ModelForm):
    ACTION_CHOICES = [
        (1, 'Create'),
        # (2, 'Delete'),
    ]

    OBJ_CHOICES = [
        (1, 'Contact Profiles'),
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
                    reverse_lazy('contacts', kwargs={}), 'Cancel')
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


class VerifyForm(forms.ModelForm):
    pass


@login_required
def simple_upload(request, template_name='contacts/upload_csv.html'):
    csv_subs_len = 2
    csv_group_len = 6
    csv_contact_len = 11

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            myfile = request.FILES['docfile']
            actobj = form.cleaned_data.get('action') + \
                form.cleaned_data.get('object')

            reader = csv.reader(io.StringIO(myfile.read().decode('utf-8')))
            headers = next(reader)  # handle row header

            items_to_verify = []
            items_in_conflict = []
            if actobj == '11':  # Create contacts
                if len(headers) < csv_contact_len:
                    myfile.close()
                    alerts.warning(request, _(
                        "Missing required headers/fields. "
                        "Check your CSV file again."
                    ))
                    return redirect('contacts')

                for row in reader:
                    if len(row) < csv_group_len:
                        break  # do nothing #TODO: add to "invalid" list

                    try:
                        contact_sim = ContactSimcards.objects.get(
                            contact__callerid=row[9])
                    except ContactSimcards.DoesNotExist:
                        contact_sim = None

                    # diff user/uuid -- attempting to transfer to another sub
                    if contact_sim and (
                            contact_sim.contact_profile.uuid != int(row[8])):
                        # TODO: Improve this!
                        items_to_verify.append(row)
                        items_in_conflict.append([
                            contact_sim.contact_profile.uuid,
                            contact_sim.contact_profile.firstname,
                            contact_sim.contact_profile.lastname,
                            contact_sim.contact_profile.nickname,
                            contact_sim.contact_profile.age,
                            contact_sim.contact_profile.gender,
                            contact_sim.contact_profile.municipality,
                            contact_sim.contact_profile.barangay,
                            contact_sim.contact_profile.sitio,
                            contact_sim.contact.callerid,
                            contact_sim.contact.imsi]
                        )

                    else:
                        try:
                            (contact_profile,
                             created) = ContactProfile.objects.update_or_create(
                                uuid=row[8],
                                defaults={
                                    'firstname': row[0],
                                    'lastname': row[1],
                                    'nickname': row[2],
                                    'age': row[3],
                                    'gender': row[4],
                                    'municipality': row[5],
                                    'barangay': row[6],
                                    'sitio': row[7],
                                    'uuid': row[8],
                                }
                            )
                            if row[9] and row[10]:
                                (contact,
                                 created) = Contact.objects.update_or_create(
                                    callerid=row[9],
                                    defaults={
                                        'callerid': row[9],
                                        'imsi': row[10]
                                    }
                                )
                                ContactSimcards.objects.update_or_create(
                                    contact=contact,
                                    contact_profile=contact_profile
                                )
                        except Exception as e:
                            print (e)
                            items_to_verify.append(row)
                            items_in_conflict.append(None)

            else:
                pass

            myfile.close()

            if items_to_verify:
                request.session['list'] = items_to_verify
                request.session['conflict'] = items_in_conflict
                return redirect(upload_verify)
            else:
                alerts.success(
                    request,
                    _("Batch operation completed successfully."))
            return redirect('contacts')
    else:
        form = DocumentForm()
    return render(request, template_name, {'form': form})


@login_required
def upload_verify(request, template_name='contacts/verify.html'):
    data = {
        'list': request.session['list'],
        'conflict': request.session['conflict'],
        'length': len(request.session['list']) * 'x'
    }
    print (request.session['conflict'])
    return render(request, template_name, data)
