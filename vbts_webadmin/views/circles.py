"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout, Submit
from dal import autocomplete
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.forms import CharField, ModelForm, Textarea, SelectMultiple
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Circle
from vbts_webadmin.models import CircleUsers
from vbts_webadmin.models import Message
from vbts_webadmin.models import MessageRecipients
from vbts_webadmin.tasks import send_sms


class CircleForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(CircleForm, self).__init__(*args, **kwargs)
        self.fields['users'].label = "Members"
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('circles', kwargs={}),
                'Cancel')
        ))

    class Meta:
        model = Circle
        exclude = ['owner']
        widgets = {
            'users': autocomplete.ModelSelect2Multiple(
                url='contact-autocomplete',
                attrs={'rows': 2}),
            'description':
                Textarea(attrs={'class': 'textinput-message', 'rows': 2})
        }


class MessageForm(ModelForm):
    text = _("Maximum 140 characters. Members won't be able to reply.")
    message = CharField(required=True, max_length=140, help_text=text,
                        widget=Textarea(
                            attrs={'class': 'textinput-message', 'rows': 2}))

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Send'))
        self.helper.layout = Layout('message')

    class Meta:
        model = Message
        fields = ['message']


class BroadcastForm(ModelForm):
    circles = CharField(
        widget=SelectMultiple(
            choices=[], attrs={
                'class': 'circle-selectmultiple'}))

    text = _("Maximum 140 characters. Members won't be able to reply.")
    message = CharField(required=True, max_length=140, help_text=text,
                        widget=Textarea(
                            attrs={'class': 'textinput-message', 'rows': 4}))

    def __init__(self, *args, **kwargs):
        initial = [kwargs.pop('circle_id')]
        super(BroadcastForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'circles',
            'recipients',
            'message',
        ]
        choices = [(x.id, x.name) for x in Circle.objects.all()]
        self.fields[
            'circles'] = CharField(widget=SelectMultiple(
                choices=choices, attrs={'class': 'circle-selectmultiple'}))
        self.fields['circles'].choices = [(x.id, x.name)
                                          for x in Circle.objects.all()]
        self.fields['circles'].initial = initial
        self.helper = FormHelper(self)
        self.helper.layout.append(Submit('circle_broadcast', 'Send Message'))

    class Meta:
        model = Message
        fields = ['circles', 'message']
        widgets = {
            'message': Textarea(attrs={'rows': 4}),
        }


@login_required
def circle_list(request, template_name='circles/list.html'):
    data = {}
    if 'search' in request.GET:
        circles = Circle.objects.filter(
            Q(name__icontains=request.GET['search']) | Q(
                owner__username__icontains=request.GET['search']))
        data['search'] = True
        alerts.info(
            request, _("You've searched for: '%s'") % request.GET['search'])
    else:
        circles = Circle.objects.all()

    paginator = Paginator(circles, 15)
    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        circles = paginator.page(page)
    except PageNotAnInteger:
        circles = paginator.page(1)
    except EmptyPage:
        circles = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='circles')
    data['circles'] = circles
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def circle_view(request, pk, template_name='circles/detail.html'):
    circle = get_object_or_404(Circle, pk=pk)
    form = MessageForm(request.POST or None)
    sender = request.user.userprofile.contact

    if form.is_valid():

        message = Message.objects.create(author=sender,
                                         message=form.cleaned_data.get(
                                             'message'))
        message.published_date = datetime.now()
        message.save()
        members = CircleUsers.objects.filter(circle_id=circle.id)
        for member in members:
            MessageRecipients.objects.create(message=message,
                                             user=member.user)
            send_sms.delay(member.user.callerid,
                           sender.callerid,
                           message.message)
        alerts.success(
            request, _("You've successfully broadcasted to  %s's members.") %
            circle.name)
    return render(request, template_name, {'circle': circle, 'form': form})


@login_required
def circle_create(request, template_name='circles/form.html'):
    form = CircleForm(request.POST or None)
    if form.is_valid():
        circle = form.save(commit=False)
        circle.owner = request.user
        circle.save()
        for member in form.cleaned_data.get('users'):
            member = CircleUsers.objects.create(user=member, circle=circle)
            member.save()
        alerts.success(request, _("You've successfully created circle '%s.'")
                       % circle.name)
        return circle_list(request)
    return render(request, template_name, {'form': form})


@login_required
def circle_update(request, pk, template_name='circles/form.html'):
    circle = get_object_or_404(Circle, pk=pk)
    form = CircleForm(request.POST or None, instance=circle)
    if form.is_valid():
        temp = form.save(commit=False)
        temp.save()
        circle.users.clear()
        for member in form.cleaned_data.get('users'):
            member = CircleUsers.objects.create(user=member, circle=circle)
            member.save()
        alerts.success(request, _("You've successfully updated circle '%s.'")
                       % circle.name)
        return circle_list(request)
    return render(request, template_name, {'form': form})


@login_required
def circle_delete(request, pk, template_name='circles/confirm_delete.html'):
    circle = get_object_or_404(Circle, pk=pk)
    if request.method == 'POST':
        circle.users.clear()
        circle.delete()
        alerts.success(request, _("You've successfully deleted circle '%s.'")
                       % circle.name)
        return circle_list(request)
    return render(request, template_name, {'circle': circle})


@login_required
def circle_broadcast(request, pk=None, template_name='circles/sms.html'):
    form = BroadcastForm(request.POST or None, circle_id=pk)
    sender = request.user.userprofile.contact

    if form.is_valid():
        message = Message.objects.create(author=sender,
                                         message=form.cleaned_data.get(
                                             'message'))
        message.published_date = datetime.now()
        message.save()
        for circle in request.POST.getlist('circles'):
            members = CircleUsers.objects.filter(circle_id=circle)
            for member in members:
                MessageRecipients.objects.create(message=message,
                                                 user=member.user)
                send_sms.delay(member.user.callerid,
                               sender.callerid,
                               message.message)
            alerts.success(request, _("You've successfully broadcasted \
                the message."))
        return circle_list(request)
    return render(request, template_name, {'form': form})
