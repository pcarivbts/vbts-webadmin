"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import absolute_import

from core import events
from core.subscriber import subscriber as endaga_sub

from celery.task.control import revoke
from crispy_forms.bootstrap import PrependedText
from crispy_forms.bootstrap import Tab
from crispy_forms.bootstrap import TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Fieldset
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.forms import ModelForm
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Promo
from vbts_webadmin.models import PromoSubscription
from vbts_webadmin.utils import float_to_mc
from vbts_webadmin.utils import mc_to_float
from vbts_webadmin.tasks import send_sms


class PromoForm(ModelForm):
    # Our temporary fields
    tmp_price = forms.DecimalField(min_value=0.1, label='Price')

    disc_local_sms = forms.DecimalField(
        min_value=0, required=False, label='Promo rate for local SMS')
    disc_local_call = forms.DecimalField(
        min_value=0, required=False, label='Promo rate for local calls')
    disc_globe_sms = forms.DecimalField(
        min_value=0, required=False, label='Promo rate for Globe SMS')
    disc_globe_call = forms.DecimalField(
        min_value=0, required=False, label='Promo rate for Globe calls')
    disc_outside_sms = forms.DecimalField(
        min_value=0, required=False, label='Promo rate for off-network SMS')
    disc_outside_call = forms.DecimalField(
        min_value=0, required=False, label='Promo rate for off-network calls')

    bulk_local_sms = forms.IntegerField(
        min_value=0, required=False, label='Local SMS')
    bulk_local_call = forms.IntegerField(
        min_value=0, required=False, label='Local Call Minutes')
    bulk_globe_sms = forms.IntegerField(
        min_value=0, required=False, label='Globe SMS')
    bulk_globe_call = forms.IntegerField(
        min_value=0, required=False, label='Globe Call Minutes')
    bulk_outside_sms = forms.IntegerField(
        min_value=0, required=False, label='Off-Network SMS')
    bulk_outside_call = forms.IntegerField(
        min_value=0, required=False, label='Off-Network Call Minutes')

    unli_local_sms = forms.BooleanField(
        required=False, label='Allow unlimited local SMS')
    unli_local_call = forms.BooleanField(
        required=False, label='Allow unlimited local calls')
    unli_globe_sms = forms.BooleanField(
        required=False, label='Allow unlimited Globe SMS')
    unli_globe_call = forms.BooleanField(
        required=False, label='Allow unlimited Globe calls')
    unli_outside_sms = forms.BooleanField(
        required=False, label='Allow unlimited Off-network SMS')
    unli_outside_call = forms.BooleanField(
        required=False, label='Allow unlimited Off-network calls')

    def __init__(self, *args, **kwargs):
        super(PromoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            Fieldset("Basic Information",
                     Field('name', placeholder="Ex: My Awesome Promo"),
                     Field('description',
                           placeholder="Ex: Get Unilimited texts to all "
                                       "networks for just 10 pesos. "
                                       "Valid for 1 day"),
                     Field('keyword', placeholder="Ex: AWESOME10"),
                     # Field('number', placeholder="Ex: 555"),
                     ),
            Fieldset("Customize your promo",
                     PrependedText('tmp_price', 'Php'),
                     PrependedText('validity', 'in days'),
                     'promo_type',
                     HTML('<div id="tabs">'),
                     TabHolder(
                         Tab('Configure your Unlimited promo',
                             'unli_local_sms',
                             'unli_local_call',
                             'unli_globe_sms',
                             'unli_globe_call',
                             'unli_outside_sms',
                             'unli_outside_call',
                             ),
                         Tab('Configure your Discounted promo',
                             PrependedText('disc_local_sms', 'Php'),
                             PrependedText('disc_local_call', 'Php'),
                             PrependedText('disc_globe_sms', 'Php'),
                             PrependedText('disc_globe_call', 'Php'),
                             PrependedText('disc_outside_sms', 'Php'),
                             PrependedText('disc_outside_call', 'Php'),
                             ),
                         Tab('Configure your Bulk promo',
                             'bulk_local_sms',
                             'bulk_local_call',
                             'bulk_globe_sms',
                             'bulk_globe_call',
                             'bulk_outside_sms',
                             'bulk_outside_call',
                             ),
                     ),
                     HTML("</div>"),
                     ),
            Submit('save', 'Save'),
            HTML(
                '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                    reverse_lazy('promos', kwargs={}), 'Cancel')
            )
        )

        # Rename fields
        self.fields['keyword'].label = "Keyword (must be in ALL CAPS)"

        if self.instance:  # meaning, we should be in promo_update view
            self.fields['tmp_price'].initial = mc_to_float(self.instance.price)
            # Need to display to user saved values for these fields
            # and do required inverse data type transformation
            for attr in ['local_sms', 'local_call',
                         'globe_sms', 'globe_call',
                         'outside_sms', 'outside_call']:
                diskey = 'disc_' + attr
                bulkey = 'bulk_' + attr
                unlkey = 'unli_' + attr
                # DISCOUNTED
                if self.instance.promo_type in ['D', 'G']:
                    self.fields[diskey].initial = \
                        mc_to_float(eval('self.instance.' + attr))
                # UNLI
                elif self.instance.promo_type == 'U':
                    self.fields[unlkey].initial = \
                        bool(eval('self.instance.' + attr))
                # BULK
                else:
                    self.fields[bulkey].initial = eval('self.instance.' + attr)

    def process_fields(self):
        """ Lets do the required data type transformation """
        self.cleaned_data['price'] = float_to_mc(
            self.cleaned_data['tmp_price'])
        for attr in ['local_sms', 'local_call',
                     'globe_sms', 'globe_call',
                     'outside_sms', 'outside_call']:
            diskey = 'disc_' + attr
            bulkey = 'bulk_' + attr
            unlkey = 'unli_' + attr
            # DISCOUNTED
            if self.cleaned_data['promo_type'] in ['D', 'G']:
                self.cleaned_data[attr] = float_to_mc(
                    self.cleaned_data[diskey])
            # UNLI
            elif self.cleaned_data['promo_type'] == 'U':
                self.cleaned_data[attr] = int(self.cleaned_data[unlkey])
            # BULK
            else:
                self.cleaned_data[attr] = self.cleaned_data[bulkey]

    def clean_keyword(self):
        return self.cleaned_data['keyword'].upper()

    def clean_validity(self):
        if self.cleaned_data['validity'] < 1:
            raise ValidationError(_("Validity must be at least 1 day."))
        else:
            return self.cleaned_data['validity']

    def clean(self):
        msg = _("You must not leave one of these fields empty.")

        if self.cleaned_data['promo_type'] in ['D', 'G']:
            if not (self.cleaned_data['disc_local_sms'] or
                    self.cleaned_data['disc_local_call'] or
                    self.cleaned_data['disc_globe_sms'] or
                    self.cleaned_data['disc_globe_call'] or
                    self.cleaned_data['disc_outside_sms'] or
                    self.cleaned_data['disc_outside_call']):
                raise ValidationError({
                    'disc_local_sms': msg,
                    'disc_local_call': msg,
                    'disc_globe_sms': msg,
                    'disc_globe_call': msg,
                    'disc_outside_call': msg,
                    'disc_outside_sms': msg})
        elif self.cleaned_data['promo_type'] == 'B':
            if not (self.cleaned_data['bulk_local_sms'] or
                    self.cleaned_data['bulk_local_call'] or
                    self.cleaned_data['bulk_globe_sms'] or
                    self.cleaned_data['bulk_globe_call'] or
                    self.cleaned_data['bulk_outside_sms'] or
                    self.cleaned_data['bulk_outside_call']):
                raise ValidationError({
                    'bulk_local_sms': msg,
                    'bulk_local_call': msg,
                    'bulk_globe_sms': msg,
                    'bulk_globe_call': msg,
                    'bulk_outside_call': msg,
                    'bulk_outside_sms': msg})

        elif self.cleaned_data['promo_type'] == 'U':
            if not (self.cleaned_data['unli_local_sms'] or
                    self.cleaned_data['unli_local_call'] or
                    self.cleaned_data['unli_globe_sms'] or
                    self.cleaned_data['unli_globe_call'] or
                    self.cleaned_data['unli_outside_sms'] or
                    self.cleaned_data['unli_outside_call']):
                raise ValidationError({
                    'unli_local_sms': msg,
                    'unli_local_call': msg,
                    'unli_globe_sms': msg,
                    'unli_globe_call': msg,
                    'unli_outside_call': msg,
                    'unli_outside_sms': msg,
                })
        else:
            return

    def is_valid(self):
        """ Need to check for blank input, since the temporary fields interpret
            them as None instead of zero.
        """
        valid = super(PromoForm, self).is_valid()
        if not valid:
            return valid

        # if we find blank fields in disc or bulk fields, we accept them
        # and set them to zero so that Django forms wont complain
        for attr in [
            'local_sms',
            'local_call',
            'globe_sms',
            'globe_call',
            'outside_sms',
                'outside_call']:
            diskey = 'disc_' + attr
            bulkey = 'bulk_' + attr
            # unlkey = 'unli_' + attr
            # DISCOUNTED
            if self.cleaned_data['promo_type'] in ['D', 'G']:
                if self.cleaned_data[diskey] is None:
                    self.cleaned_data[diskey] = 0
            # BULK
            elif self.cleaned_data['promo_type'] == 'B':
                if self.cleaned_data[bulkey] is None:
                    self.cleaned_data[bulkey] = 0
            # UNLI
            # else: we allow unli checkboxes to be unchecked, since an unchecked
            # box is interpreted as False
        return True

    def save(self, commit=True):
        """ Custom save method.
            Lets process the data first from our temporary fields and then
            copy them to the promo model fields.
        """
        instance = super(PromoForm, self).save(commit=False)
        self.process_fields()
        instance.keyword = self.cleaned_data['keyword'].upper()
        instance.price = self.cleaned_data['price']
        instance.local_sms = self.cleaned_data['local_sms']
        instance.local_call = self.cleaned_data['local_call']
        instance.globe_sms = self.cleaned_data['globe_sms']
        instance.globe_call = self.cleaned_data['globe_call']
        instance.outside_sms = self.cleaned_data['outside_sms']
        instance.outside_call = self.cleaned_data['outside_call']
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Promo
        exclude = ['author', 'subscribers', 'price', 'number',
                   'local_sms', 'local_call', 'globe_sms', 'globe_call',
                   'outside_sms', 'outside_call']


@login_required
def promo_list(request, template_name='promos/list.html'):
    data = {}
    if 'search' in request.GET:
        promos = Promo.objects.all()
        for term in request.GET['search'].split():
            promos = promos.filter(Q(name__icontains=term) |
                                   Q(description__icontains=term))

        data['search'] = True
        alerts.info(request,
                    _("You've searched for: '%s'") % request.GET['search'])
    else:
        promos = Promo.objects.all()

    paginator = Paginator(promos, 15)

    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        promos = paginator.page(page)
    except PageNotAnInteger:
        promos = paginator.page(1)
    except EmptyPage:
        promos = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='promos')
    data['promos'] = promos
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def promo_view(request, pk, template_name='promos/detail.html'):
    promo = get_object_or_404(Promo, pk=pk)
    subscription = PromoSubscription.objects.filter(promo_id=pk)
    paginator = Paginator(subscription, 15)

    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        subscription = paginator.page(page)
    except PageNotAnInteger:
        subscription = paginator.page(1)
    except EmptyPage:
        subscription = paginator.page(paginator.num_pages)
    data = {
        'promo': promo,
        'subscription': subscription,
        'is_paginated': is_paginated
    }
    return render(request, template_name, data)


@login_required
def promo_create(request, template_name='promos/form.html'):
    form = PromoForm(request.POST or None)
    if form.is_valid():
        promo = form.save(commit=False)
        promo.author = request.user
        promo.save()
        alerts.success(request, _("You've successfully created promo '%s.'")
                       % promo.name)
        return redirect('promos')
    else:
        alerts.warning(request, _("Please input the required fields below."))
    return render(request, template_name, {'form': form})


@login_required
def promo_update(request, pk, template_name='promos/form.html'):
    promo = get_object_or_404(Promo, pk=pk)
    form = PromoForm(request.POST or None, instance=promo)
    if form.is_valid():
        form.save()
        alerts.success(request, _("You've successfully updated promo '%s.'")
                       % promo.name)
        return redirect('promos')
    else:
        alerts.warning(request, _("Please input the required fields below."))
    return render(request, template_name, {'form': form})


@login_required
def promo_delete(request, pk, template_name='promos/confirm_delete.html'):
    promo = get_object_or_404(Promo, pk=pk)
    if request.method == 'POST':
        promo.delete()
        alerts.success(request, _("You've successfully deleted promo '%s.'")
                       % promo.name)
        return redirect('promos')
    return render(request, template_name, {'promo': promo})


@login_required
def promo_delete_subscription(
        request, pk, template_name='promos/subscription_'
        'confirm_delete.html'):
    subscription = get_object_or_404(PromoSubscription, pk=pk)
    if request.method == 'POST':
        revoke(str(pk), terminate=True)
        msg = _("You were automatically unsubscribed from your %s promo."
                ) % subscription.promo.keyword
        send_sms.delay(subscription.contact.callerid, '0000', msg)

        # we should also create an event
        balance = endaga_sub.get_account_balance(subscription.contact.imsi)
        reason = "Promo Cancel Subscription: %s" % subscription.promo.keyword
        events.create_sms_event(subscription.contact.imsi, balance,
                                0, reason, '555')

        subscription.delete()
        return redirect(request.GET.get('from', 'promos'))
    return render(request, template_name, {'subscription': subscription})


@login_required
def promo_view_subscriptions(request, template_name='promos/'
                                                    'view_subscriptions.html'):
    subscription = PromoSubscription.objects.all()
    paginator = Paginator(subscription, 15)

    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        subscription = paginator.page(page)
    except PageNotAnInteger:
        subscription = paginator.page(1)
    except EmptyPage:
        subscription = paginator.page(paginator.num_pages)
    data = {
        'subscription': subscription,
        'is_paginated': is_paginated
    }
    return render(request, template_name, data)
