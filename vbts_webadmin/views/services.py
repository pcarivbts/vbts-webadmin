"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import os
import json

from crispy_forms.bootstrap import PrependedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Fieldset
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from dal import autocomplete
from django.conf import settings
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.forms import CharField, ModelForm, Textarea, ChoiceField, \
    IntegerField, DecimalField, ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Template, Context
from django.utils import timezone
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Message, MessageRecipients
from vbts_webadmin.models import Service, ServiceSubscribers
from vbts_webadmin.models import ServiceScheduledTasks
from vbts_webadmin.tasks import reload_fs_xml
from vbts_webadmin.tasks import send_sms
from vbts_webadmin.utils import create_periodic_task
from vbts_webadmin.utils import float_to_mc
from vbts_webadmin.utils import mc_to_float
from vbts_webadmin.widgets import JSON2DArrayWidget


class MessageForm(ModelForm):
    text = _("Maximum 140 characters. Subscribers won't be able to reply.")
    message = CharField(
        required=True, label="Message", max_length=140, help_text=text,
        widget=Textarea(attrs={'class': 'textinput-message', 'rows': 2}))

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Send'))
        self.helper.layout = Layout('message')

    class Meta:
        model = Message
        fields = ['message']


class ServiceForm(ModelForm):
    PERIOD_CHOICES = (
        ('days', 'day(s)'),
        ('hours', 'hour(s)'),
        ('minutes', 'minute(s)'),
        ('seconds', 'second(s)'),
    )
    period = ChoiceField(
        choices=PERIOD_CHOICES,
        required=False,
        label='Period')
    every = IntegerField(min_value=1, required=False, label='Every')
    tmp_price = DecimalField(min_value=0.1,
                             required=True,
                             label='Price per request')

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.fields['script'].empty_label = "Please select a script."
        self.helper.layout = Layout(
            Fieldset("Basic Information",
                     Field('name', placeholder="Ex: My Awesome Service"),
                     Field('description',
                           placeholder="Ex: Sample Description"),
                     Field('keyword', placeholder="Ex: AWESOME"),
                     Field('number', placeholder="Ex: 555"),
                     PrependedText('tmp_price', 'Php'),
                     ),
            Fieldset("Service Feature",
                     'script',
                     'service_type',
                     HTML('<div class="panel-body" id="sked">'),
                     HTML('<p class="text-muted">Please set the interval'
                          ' schedule for sending push messages.</p>'),
                     'every',
                     'period',
                     HTML("</div>"),
                     ),
            Submit('save', 'Save')
        )

        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if instance.service_type == 'P':
                interval = ServiceScheduledTasks.objects.get(
                    service=instance).get_interval()
                self.fields['every'].initial = interval.every
                self.fields['period'].initial = interval.period

            self.fields['tmp_price'].initial = mc_to_float(
                self.instance.price)
            self.fields['script'].required = False
            self.fields['script'].widget.attrs['disabled'] = 'disabled'
            self.fields['service_type'].required = False
            self.fields['service_type'].widget.attrs['disabled'] = 'disabled'
            self.helper.layout.append(
                HTML('<a class="btn btn-default" href="{}">{}</a>'.format(
                    reverse_lazy('service_detail',
                                 kwargs={'pk': instance.pk}),
                    'Cancel')
                )
            )

        else:
            self.helper.layout.append(
                HTML(
                    '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                        reverse_lazy(
                            'services',
                            kwargs={}),
                        'Cancel')))

    def clean_tmp_price(self):
        if not self.cleaned_data['tmp_price']:
            raise ValidationError(_('This field is required.'))
        return self.cleaned_data['tmp_price']

    def clean_script(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.script
        else:
            return self.cleaned_data['script']

    def clean_keyword(self):
        return self.cleaned_data['keyword'].upper()

    def clean_every(self):
        if self.cleaned_data['service_type'] == 'P':
            if not self.cleaned_data['every']:
                raise ValidationError(_('This field is required.'))
        return self.cleaned_data['every']

    def save(self, commit=True):
        instance = super(ServiceForm, self).save(commit=False)
        instance.price = float_to_mc(self.cleaned_data['tmp_price'])
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Service
        fields = ['name', 'script', 'description', 'keyword', 'number',
                  'service_type']
        exclude = ['chatplan', 'managers', 'script_arguments', 'status']
        widgets = {
            'managers': autocomplete.ModelSelect2Multiple(
                url='contact-autocomplete'),
            'description': Textarea(attrs={'rows': 4}),
        }


class ServiceScriptForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(ServiceScriptForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.fields['script_arguments'].help_text = ''
        instance = getattr(self, 'instance', None)
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(
            HTML('<a class="btn btn-danger" href="{}">{}</a>&nbsp;'.format(
                reverse_lazy('service_reset', kwargs={'pk': instance.pk}),
                'Reset')))
        self.helper.layout.append(
            HTML('<a class="btn btn-default" href="{}">{}</a>'.format(
                reverse_lazy('service_detail', kwargs={'pk': instance.pk}),
                'Cancel')))

    class Meta:
        model = Service
        fields = ['script_arguments']
        widgets = {
            'script_arguments': JSON2DArrayWidget(debug=False)
        }


@login_required
def service_list(request, template_name='services/list.html'):
    data = {}
    if 'search' in request.GET:
        services = Service.objects.filter(
            Q(name__icontains=request.GET['search']))
        data['search'] = True
        alerts.info(request,
                    _("You've searched for: '%s'") % request.GET['search'])
    else:
        services = Service.objects.all()

    paginator = Paginator(services, 15)

    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        services = paginator.page(page)
    except PageNotAnInteger:
        services = paginator.page(1)
    except EmptyPage:
        services = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='services')
    data['services'] = services
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def service_view(request, pk, template_name='services/detail.html'):
    service = get_object_or_404(Service, pk=pk)

    form = MessageForm(request.POST or None)
    sender = request.user.userprofile.contact

    if form.is_valid() and 'submit' in request.POST and 'message' in request.POST:

        message = Message.objects.create(author=sender,
                                         message=form.cleaned_data.get(
                                             'message'))
        message.published_date = timezone.now()
        message.save()
        subscribers = ServiceSubscribers.objects.filter(service_id=service.id)
        for subscriber in subscribers:
            MessageRecipients.objects.create(message=message,
                                             user=subscriber.subscriber)
            send_sms.delay(subscriber.subscriber.callerid,
                           sender.callerid,
                           message.message)
        alerts.success(request,
                       _("You've successfully broadcasted to "
                         "%s's subscribers") % service)

    data = {
        'service': service,
        'script_args': json.dumps(service.script_arguments),
        'form': form
    }
    if service.service_type == 'P':
        data['interval'] = ServiceScheduledTasks.objects.get(
            service=service).get_interval()
    return render(request, template_name, data)


@login_required
def service_create(request, template_name='services/form.html'):
    form = ServiceForm(request.POST or None)
    if form.is_valid():
        service = form.save(commit=False)
        service.author = request.user
        service.published_date = timezone.now()
        service.script_arguments = service.script.arguments
        service.save()
        util_create_or_update(service,
                              form.cleaned_data.get('every'),
                              form.cleaned_data.get('period'))
        alerts.success(
            request,
            _("You've successfully created '%s' service.") %
            service)
        return redirect('services')
    return render(request, template_name, {'form': form})


@login_required
def service_delete(request, pk, template_name='services/confirm_delete.html'):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        util_delete(service)
        service.delete()
        alerts.success(request,
                       _("You've successfully deleted '%s' service.") %
                       service)
        return redirect('services')
    return render(request, template_name, {'service': service})


@login_required
def service_publish(request, pk, template_name='services/publish.html'):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST' and 'status' in request.POST:
        service.status = request.POST.get("status")
        service.save()
        status = util_publish(service)
        service.save()
        message = _("You've successfully %(status)s '%(service)s' "
                    "service.") % ({'status': status,
                                    'service': service})
        alerts.success(request, message)
        return redirect('services')
    return render(request, template_name, {'service': service})


@login_required
def service_update_script_props(request, pk,
                                template_name='services/form_props.html'):
    service = get_object_or_404(Service, pk=pk)
    form = ServiceScriptForm(request.POST or None, instance=service)
    if form.is_valid():
        form.save()
        alerts.success(request,
                       _("You've successfully updated '%s' service.") %
                       service)
    return render(request, template_name, {'form': form, 'service': service})


@login_required
def service_reset_script_props(request, pk,
                               template_name='services/reset.html'):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST' and 'reset' in request.POST:
        service.script_arguments = service.script.arguments
        service.save()
        alerts.success(request,
                       _("You've successfully reset '%s' service.") %
                       service)
    return render(request, template_name, {'service': service})


@login_required
def service_update(request, pk, template_name='services/form.html'):
    service = get_object_or_404(Service, pk=pk)
    form = ServiceForm(request.POST or None, instance=service)
    if form.is_valid():
        form.save()
        util_create_or_update(service, form.cleaned_data.get('every'),
                              form.cleaned_data.get('period'),
                              update=True)
        alerts.success(request,
                       _("You've successfully updated '%s' service.") %
                       service)
        return service_view(request, service.pk)
    return render(request, template_name, {'form': form})


#
#    Utilities to do corresponding CRUD to chatplans or periodic tasks
#

def create_chatplan(instance):
    try:
        template = os.path.join(
            settings.PCARI['CHATPLAN_TEMPLATES_DIR'],
            instance.script.chatplan)
        fp = open(template)
        t = Template(fp.read())
        fp.close()
        xml = t.render(
            Context({'keyword': instance.keyword, 'number': instance.number,
                     'price': instance.price}))

        instance.chatplan = '16_SERVICE_%s.xml' % instance.keyword
        instance.save()

        # create the chatplan
        chatplan_path = os.path.join(settings.CHATPLAN_DIR,
                                     instance.chatplan)

        f = open(chatplan_path, 'w')
        myfile = File(f)
        myfile.write(xml)
        myfile.close()

        reload_fs_xml.delay()
    except BaseException:
        pass


def delete_chatplan(instance):
    try:
        if instance.chatplan:
            chatplan_path = os.path.join(settings.CHATPLAN_DIR,
                                         instance.chatplan)
            os.remove(chatplan_path)
            reload_fs_xml.delay()
    except OSError:
        pass


def util_create_or_update(instance, every, period, update=False):
    """
        Utility function to created needed schedules or chatplans
    Args:
        instance: the service object instance
        every: integer value, ie: 30
        period: interval period for schedule: ie: days
        update: boolen, set to TRUE when updating so that
                additional stuff will be executed

    Returns:
        None
    """
    if instance.service_type == 'P':  # Push message
        if update:
            ServiceScheduledTasks.objects.get(service=instance).edit(period,
                                                                     every)
        else:
            task = create_periodic_task(
                task_name='vbts_webadmin.tasks.push_cmd_routine',
                every=every,
                period=period,
                args=[instance.id])
            ServiceScheduledTasks.objects.create(service=instance,
                                                 periodic_task=task)

    elif instance.service_type == 'I':  # Info message
        # IF PUBLISHED, update chatplan, ELSE DO NOT CREATE CHATPLAN
        if instance.status == 'P':
            if instance.chatplan:  # this is an update, remove old one
                delete_chatplan(instance)
            create_chatplan(instance)


def util_delete(service):
    """
        Utility function that performs the schedule or chatplan deletion
    Args:
        service: the service object

    Returns:
        None
    """
    if service.service_type == 'P':
        ServiceScheduledTasks.objects.get(service=service).terminate()

    elif service.service_type == 'I':
        delete_chatplan(instance=service)


def util_publish(service):
    """
        Utility function to change publishing status
    Args:
        service: the service object

    Returns:
        status:
    """
    if service.service_type == 'P':  # Push Message
        if service.status == "P":
            status = "published"
            ServiceScheduledTasks.objects.get(service=service).start()
        else:
            status = "unpublished"
            ServiceScheduledTasks.objects.get(service=service).stop()

    elif service.service_type == 'I':  # Info Request
        if service.status == "P":
            status = "published"
            create_chatplan(service)
        else:
            status = "unpublished"
            delete_chatplan(service)

    return status
