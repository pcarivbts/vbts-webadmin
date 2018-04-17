"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from datetime import timedelta

from core import events
from core.subscriber import subscriber as endaga_sub
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
from django.forms import TextInput
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone as timezone
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Contact
from vbts_webadmin.models import ContactProfile
from vbts_webadmin.models import ContactSimcards
from vbts_webadmin.models import Group
from vbts_webadmin.models import PromoSubscription
from vbts_webadmin.models import ServiceSubscribers
from vbts_webadmin.tasks import purge_entry
from vbts_webadmin.tasks import send_sms


class ContactForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('contacts', kwargs={}),
                'Cancel')
        ))

    class Meta:
        model = ContactProfile
        exclude = ['contact']
        widgets = {
            'birthdate': TextInput(attrs={'class': 'datepicker'})
        }


class ContactAddPromoForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.contact = kwargs.pop('contact')
        super(ContactAddPromoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.fields['contact'].label = "SIM Card"
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('contacts', kwargs={}),
                'Cancel')
        ))

        if self.contact:
            self.fields['contact'].initial = self.contact

    class Meta:
        model = PromoSubscription
        fields = ['contact', 'promo']
        widgets = {}


class ContactAssignProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.contact = kwargs.pop('contact')
        super(ContactAssignProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('contacts', kwargs={}),
                'Cancel')
        ))

        if self.contact:
            self.fields['contact'].initial = self.contact

    class Meta:
        model = ContactSimcards
        fields = ['contact', 'contact_profile']
        widgets = {}


@login_required
def contact_list(request, template_name='contacts/list.html'):
    data = {}
    if 'search' in request.GET:
        contacts_sims = ContactSimcards.objects.all()
        contacts_sims_imsi = ContactSimcards.objects.values_list('contact_id',
                                                                 flat=True)
        no_profiles = Contact.objects.exclude(imsi__in=contacts_sims_imsi)
        unreg_sims = no_profiles.filter(Q(imsi__icontains='IMSI'))
        offnets = no_profiles.filter(Q(imsi__icontains='OFFNET'))
        profiles = ContactProfile.objects.all()

        for term in request.GET['search'].split():
            contacts_sims = contacts_sims.filter(
                Q(contact_profile__firstname__icontains=term) |
                Q(contact_profile__lastname__icontains=term) |
                Q(contact__callerid__icontains=term))
            unreg_sims = unreg_sims.filter(
                Q(callerid__icontains=term) |
                Q(imsi__icontains=term))
            offnets = offnets.filter(
                Q(callerid__icontains=term) |
                Q(imsi__icontains=term))

        data['search'] = True
        alerts.info(request,
                    _("You've searched for: '%s'") % request.GET['search'])
    else:
        contacts_sims = ContactSimcards.objects.all()
        contacts_sims_imsi = ContactSimcards.objects.values_list('contact_id',
                                                                 flat=True)
        no_profiles = Contact.objects.exclude(imsi__in=contacts_sims_imsi)
        unreg_sims = no_profiles.filter(Q(imsi__icontains='IMSI'))
        offnets = no_profiles.filter(Q(imsi__icontains='OFFNET'))
        profiles = ContactProfile.objects.all()

    paginator = Paginator(contacts_sims, 15)
    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        contacts_sims = paginator.page(page)
    except PageNotAnInteger:
        contacts_sims = paginator.page(1)
    except EmptyPage:
        contacts_sims = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='contacts')
    data['contacts_sims'] = contacts_sims
    data['is_paginated'] = is_paginated
    data['form'] = form
    data['unreg_sims'] = unreg_sims
    data['offnets'] = offnets
    data['profiles'] = profiles
    return render(request, template_name, data)


@login_required
def contact_view(request, pk, template_name='contacts/detail.html'):
    contact_profile = get_object_or_404(ContactProfile, id=pk)
    sims = ContactSimcards.objects.filter(contact_profile=contact_profile)
    contacts = ContactSimcards.objects.filter(
        contact_profile=contact_profile).values_list('contact', flat=True)
    promo_subscription = PromoSubscription.objects.filter(contact=contacts)
    service_subscription = ServiceSubscribers.objects.filter(
        subscriber=contacts)
    try:
        # group = ContactProfile.objects.filter(
            # contact__in=Group.objects.get(owner=contacts).members.all())
        group = Group.objects.get(owner=contacts)
    except Group.DoesNotExist:
        group = None

    data = {
        'contact_profile': contact_profile,
        'sims': sims,
        'promo_subscription': promo_subscription,
        'service_subscription': service_subscription,
        'group': group,
    }
    return render(request, template_name, data)


@login_required
def contact_create(request, template_name='contacts/form.html'):
    form = ContactForm(request.POST or None)
    if form.is_valid():
        instance = form.save()
        alerts.success(
            request,
            _("You've successfully created contact '%s.'") % instance
        )
        return contact_list(request)
    return render(request, template_name, {'form': form})


@login_required
def contact_create_profile(request, pk, template_name='contacts/form.html'):
    form = ContactForm(request.POST or None)
    if form.is_valid():
        instance = form.save()
        ContactSimcards.objects.create(
            contact=Contact.objects.get(callerid=pk),
            contact_profile=instance
        )
        alerts.success(
            request,
            _("You've successfully created contact '%s.'") % instance
        )
        return contact_list(request)
    return render(request, template_name, {'form': form})


@login_required
def contact_update(request, pk, template_name='contacts/form.html'):
    contact_profile = get_object_or_404(ContactProfile, id=pk)
    form = ContactForm(request.POST or None, instance=contact_profile)
    if form.is_valid():
        form.save()
        alerts.success(
            request,
            _("You've successfully updated contact '%s.'") % contact_profile
        )
        return contact_list(request)
    return render(request, template_name, {'form': form})


@login_required
def contact_delete(request, pk, template_name='contacts/confirm_delete.html'):
    contact_profile = get_object_or_404(ContactProfile, id=pk)
    if request.method == 'POST':
        contact_profile.delete()
        alerts.success(
            request,
            _("You've successfully deleted contact '%s.'") % contact_profile
        )
        return contact_list(request)
    return render(request, template_name, {'contact_profile': contact_profile})


@login_required
def add_promo(request, pk=None, template_name='contacts/addpromo_form.html'):
    """
        This function ties a promo (creates a promo subscription)
        to a SIM card (Contact)
    Args:
        request:
        pk: primary key passed is the SIM card's callerid
        template_name:

    Returns:

    """
    if pk:
        contact = get_object_or_404(Contact, callerid=pk)
    else:
        contact = None
    form = ContactAddPromoForm(request.POST or None, contact=contact)

    if form.is_valid():
        instance = form.save(commit=False)
        promo = form.cleaned_data.get('promo')
        contact = form.cleaned_data.get('contact')
        instance.local_sms = promo.local_sms
        instance.local_call = promo.local_call
        instance.outside_sms = promo.outside_sms
        instance.outside_call = promo.outside_call
        instance.date_expiration = timezone.now() + timedelta(
            promo.validity)
        instance.save()

        send_sms.delay(contact.callerid, '0000',
                       _('You are automatically subscribed to %(promo)s promo. '
                         'To opt out, text REMOVE %(keyword)s to 555.') % ({
                             'promo': promo.name,
                             'keyword': promo.keyword}
                       ))
        purge_entry.apply_async(eta=instance.date_expiration,
                                args=[instance.pk],
                                task_id=str(instance.pk))

        # we should also create an event
        balance = endaga_sub.get_account_balance(contact.imsi)
        reason = "Promo Auto Subscription: %s" % promo.keyword
        events.create_sms_event(contact.imsi, balance,
                                0, reason, '555')

        alerts.success(request,
                       _("You've successfully added '%(promo)s' promo to "
                         "contact '%(contact)s.'") % ({
                             'promo': promo,
                             'contact': contact
                         }))
        return contact_list(request)
    return render(request, template_name, {'form': form})


@login_required
def contact_assign_profile(request, pk, template_name='contacts/form.html'):
    """
        This function assigns an existing registered subscriber
        (ContactProfile) to a SIM card (Contact)
    Args:
        request:
        pk: primary key passed is the SIM Card's callerid
        template_name:

    Returns:

    """
    if pk:
        contact = get_object_or_404(Contact, callerid=pk)
    else:
        contact = None
    form = ContactAssignProfileForm(request.POST or None, contact=contact)

    if form.is_valid():
        instance = form.save(commit=False)
        contact_profile = form.cleaned_data.get('contact_profile')
        contact = form.cleaned_data.get('contact')
        ContactSimcards.objects.create(
            contact=contact,
            contact_profile=contact_profile
        )
        alerts.success(
            request,
            _("You've successfully created contact '%s.'") %
            instance)
        return contact_list(request)
    return render(request, template_name, {'form': form})
