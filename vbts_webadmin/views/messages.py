"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Submit
from dal import autocomplete
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.forms import BooleanField, CheckboxInput, ModelForm, Textarea
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Contact
from vbts_webadmin.models import Message
from vbts_webadmin.models import MessageRecipients
from vbts_webadmin.tasks import send_sms


class MessageForm(ModelForm):
    to_all = BooleanField(required=False, label="Send to all subscribers?",
                          widget=CheckboxInput(
                              attrs={'class': 'to_all-checkbox'}))

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', {})
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('message_send', 'Send Message'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('messages', kwargs={}),
                'Cancel')
        ))

    def clean(self):
        cleaned_data = super(MessageForm, self).clean()
        to_all = cleaned_data.get("to_all", None)

        if to_all and "recipients" in self._errors:
            del self._errors["recipients"]

        return cleaned_data

    class Meta:
        model = Message
        fields = ['recipients', 'to_all', 'message']
        widgets = {
            'recipients': autocomplete.ModelSelect2Multiple(
                url='contact-autocomplete'),
            'message': Textarea(attrs={'rows': 4}),
        }


@login_required
def message_list(request, template_name='messages/list.html'):
    data = {}
    if 'search' in request.GET:
        # TODO: Improve this! Basically need reverse lookup
        # from contact to contactprofile
        messages = Message.objects.filter(
            Q(message__icontains=request.GET['search'])
            | Q(recipients__callerid__icontains=request.GET['search'])
            | Q(recipients__imsi__icontains=request.GET[
                'search'])).order_by('-date')
        data['search'] = True
        alerts.info(
            request, _("You've searched for: '%s'") % request.GET['search'])
    else:
        messages = Message.objects.all().order_by('-date')

    paginator = Paginator(messages, 15)

    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        messages = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='messages')
    data['smss'] = messages
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def message_view(request, pk, template_name='messages/detail.html'):
    message = get_object_or_404(Message, pk=pk)
    data = {'message': message}
    return render(request, template_name, {'message': message})


@login_required
def message_send(request, template_name='messages/form.html'):
    form = MessageForm(request.POST or None)
    if form.is_valid():
        message = form.save(commit=False)
        message.author = request.user.userprofile.contact
        message.published_date = timezone.now()
        message.save()

        if form.cleaned_data.get('to_all'):
            contacts = Contact.objects.filter(~Q(imsi=message.author.imsi))
        else:
            contacts = form.cleaned_data.get('recipients')

        for contact in contacts:
            recipient = MessageRecipients.objects.create(
                message=message, user=contact)
            recipient.save()
            send_sms.delay(contact.callerid,
                           message.author.callerid,
                           message.message)
        alerts.success(
            request,
            _("You've successfully sent the message '%s'.") %
            message.message)
        return message_list(request)
    return render(request, template_name, {'form': form})
