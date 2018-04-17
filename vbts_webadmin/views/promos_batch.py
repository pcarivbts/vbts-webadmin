"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import absolute_import

import csv
import io
from datetime import timedelta

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.conf import settings
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from django.utils.translation import ugettext as _

from vbts_webadmin.celery import app
from vbts_webadmin.models import Contact
from vbts_webadmin.models import Document
from vbts_webadmin.models import Promo
from vbts_webadmin.models import PromoSubscription
from vbts_webadmin.tasks import purge_entry
from vbts_webadmin.tasks import send_sms

from core import events
from core.subscriber import subscriber as endaga_sub


class DocumentForm(forms.ModelForm):
    ACTION_CHOICES = [
        (1, 'Create'),
        # (2, 'Delete'),
    ]

    OBJ_CHOICES = [
        (1, 'Promos'),
        (2, 'Promo Subscriptions'),
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
                    reverse_lazy('promos', kwargs={}), 'Cancel')
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
def simple_upload(request, template_name='promos/upload_csv.html'):
    csv_subs_len = 2
    csv_promo_len = 12
    fail = False
    promo = True
    contact = True
    page = 'promo_upload_csv'

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            myfile = request.FILES['docfile']
            actobj = form.cleaned_data.get(
                'action') + form.cleaned_data.get('object')

            reader = csv.reader(io.StringIO(myfile.read().decode('utf-8')))
            headers = next(reader)  # handle row header
            if actobj == '11':  # Create promos
                if len(headers) < csv_promo_len:
                    fail = True
                    alerts.warning(request, _(
                        "Missing required fields. Check your CSV file again."
                    ))
                for row in reader:
                    if len(row) < csv_promo_len:
                        break  # do nothing
                    try:
                        Promo.objects.create(
                            author=request.user,
                            name=row[0],
                            description=row[1],
                            price=row[2],
                            promo_type=row[3],
                            keyword=row[4],
                            validity=row[5],
                            local_sms=row[6],
                            local_call=row[7],
                            globe_sms=row[8],
                            globe_call=row[9],
                            outside_sms=row[10],
                            outside_call=row[11])
                    except Exception as e:
                        fail = True
                        alerts.warning(
                            request, _(
                                'Duplicate entries found in CSV file. %s' %
                                e))

            elif actobj == '12':  # Create promo subscriptions
                if len(headers) < csv_subs_len:
                    fail = True
                    alerts.warning(request, _(
                        "Missing required fields. Check your CSV file again."
                    ))
                for row in reader:
                    if len(row) < csv_subs_len:
                        break
                    try:
                        promo = Promo.objects.get(keyword=row[0])
                    except Promo.DoesNotExist:
                        promo = None
                    try:
                        contact = Contact.objects.get(callerid=row[1])
                    except Contact.DoesNotExist:
                        fail = True
                        contact = None

                    if promo and contact:
                        try:
                            instance = PromoSubscription.objects.create(
                                promo=promo,
                                contact=contact,
                                date_expiration=timezone.now() + timedelta(
                                    promo.validity),
                                local_sms=promo.local_sms,
                                local_call=promo.local_call,
                                globe_sms=promo.globe_sms,
                                globe_call=promo.globe_call,
                                outside_sms=promo.outside_sms,
                                outside_call=promo.outside_call)
                            purge_entry.apply_async(
                                eta=instance.date_expiration,
                                args=[instance.pk],
                                task_id=str(instance.pk))
                            send_sms.delay(
                                contact.callerid,
                                '0000',
                                _(
                                    'You are automatically subscribed to %(promo)s promo '
                                    'valid for %(validity)s day(s). '
                                    'To opt out, text REMOVE %(keyword)s to 555. '
                                    'For more info, text INFO %(keyword)s to 555.') % ({
                                        'promo': promo.name,
                                        'validity': promo.validity,
                                        'keyword': promo.keyword}))
                            # we should also create an event
                            balance = endaga_sub.get_account_balance(
                                contact.imsi)
                            reason = "Promo Auto Subscription: %s" % promo.keyword
                            events.create_sms_event(contact.imsi, balance,
                                                    0, reason, '555')
                        except BaseException:
                            pass

            elif actobj == '21':  # Delete promo
                pass
                # for row in reader:
                #     Promo.objects.filter(keyword=row[6]).delete()
                # # TODO: Do we also delete exisiting subscriptions?
            elif actobj == '22':  # Delete promo subscriptions
                for row in reader:
                    subscriptions = PromoSubscription.objects.filter(
                        promo__keyword__exact=row[0],
                        contact__callerid__exact=row[1])
                    for item in subscriptions:
                        app.control.revoke(str(item.id), terminate=True)
                    subscriptions.delete()
            else:
                pass

            myfile.close()
            if not fail:
                alerts.success(request, _(
                    "Batch operation completed successfully."))
                page = 'promos'
            else:
                if not contact:
                    alerts.warning(
                        request,
                        _("Operation failed. Contact does not exist.")
                    )
                elif not promo:
                    alerts.warning(
                        request,
                        _("Operation failed. Promo does not exist.")
                    )
                else:
                    alerts.warning(
                        request,
                        _("Operation failed. Unknown error.")
                    )
            return redirect(page)
    else:
        form = DocumentForm()
    return render(request, template_name, {'form': form})
