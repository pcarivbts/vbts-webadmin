"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import uuid

import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from djcelery.models import PeriodicTask, IntervalSchedule
from jsonfield import JSONField

from vbts_webadmin.utils import manage_interval


GENDER_CHOICES = (
    ('U', 'Unknown'),
    ('M', 'Male'),
    ('F', 'Female')
)

MUNICIPALITY_CHOICES = (
    ('U', 'Unknown'),
    ('S', 'San Luis'),
    ('D', 'Dingalan')
)

BRGY_CHOICES = (
    ('U', 'Unknown'),
    ('1', 'Dibut'),
    ('2', 'Dibayabay'),
    ('3', 'Dikapinsan'),
    ('4', 'Dimanayat'),
    ('5', 'Dikapanikian'),
    ('6', 'Umiray'),

)

SITIO_CHOICES = (
    ('U', 'Unknown'),
    ('1', 'Pinamaypayan'),
    ('2', 'Matinik-Singawan'),
    ('3', 'Dugyan-Lanatong'),
    ('4', 'Kamandag'),
    ('5', 'Ferry Site'),
    ('6', 'Market Site'),
    ('7', 'Bacong'),
    ('8', 'Sabang'),
    ('9', 'Limbok'),
    ('10', 'Sumalag'),
    ('11', 'Malacauayan'),
    ('12', 'School Site'),
    ('13', 'Dikapanikian Proper'),
    ('14', 'Alasanay'),
    ('15', 'Dimanayat Proper'),
    ('16', 'Labgan'),
    ('17', 'Dikapinisan Proper'),
    ('18', 'Diotorin'),
    ('19', 'Dibayabay Proper'),
    ('20', 'Dibut Proper')
)


class Contact(models.Model):
    """ The model containing information of the SIM Card """
    imsi = models.CharField(primary_key=True, max_length=19, unique=True)
    callerid = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = 'pcari_contact'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['-callerid']

    def get_profile(self):
        try:
            return ContactSimcards.objects.get(
                contact=self.imsi).contact_profile
        except ContactSimcards.DoesNotExist:
            if 'IMSI' in self.imsi:
                return 'Unregistered VBTS number'
            else:
                return 'Off-network number'

    def __unicode__(self):
        return "%s (%s)" % (self.callerid, self.get_profile())


class ContactProfile(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.PositiveIntegerField(null=False, blank=False, unique=True)
    firstname = models.CharField(max_length=80)
    lastname = models.CharField(max_length=80)
    nickname = models.CharField(max_length=80)
    age = models.PositiveIntegerField(null=False, blank=False, default=0)
    gender = models.CharField(max_length=10, blank=False, null=False,
                              choices=GENDER_CHOICES,
                              default=GENDER_CHOICES[0][1])
    municipality = models.CharField(max_length=80, blank=False, null=False,
                                    choices=MUNICIPALITY_CHOICES,
                                    default=MUNICIPALITY_CHOICES[0][1])
    barangay = models.CharField(max_length=80, blank=False, null=False,
                                choices=BRGY_CHOICES,
                                default=BRGY_CHOICES[0][1])
    sitio = models.CharField(max_length=80, blank=False, null=False,
                             choices=SITIO_CHOICES,
                             default=SITIO_CHOICES[0][1])
    contact = models.ManyToManyField(Contact, through='ContactSimcards')

    class Meta:
        db_table = 'pcari_contact_profile'
        verbose_name = 'Contact Profile'
        verbose_name_plural = 'Contact Profile'

    def __unicode__(self):
        return "%s %s" % (self.firstname, self.lastname)


class ContactSimcards(models.Model):
    contact = models.OneToOneField(Contact)
    contact_profile = models.ForeignKey(ContactProfile)
    date_registered = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'pcari_contact_simcards'
        verbose_name = "Contact's Simcard"
        verbose_name_plural = "Contact's Simcards"
        ordering = ['-id']

    # def __unicode__(self):
    #     return self.contact_profile.lastname


class UserProfile(models.Model):

    """
        UserProfiles extend the default Django User models.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    contact = models.ForeignKey('Contact',
                                null=True,
                                on_delete=models.SET_NULL)
    language = models.CharField(max_length=5, blank=True, null=True,
                                choices=settings.LANGUAGES,
                                default=settings.LANGUAGES[0][0])
    timezone = models.CharField(max_length=50, blank=True, null=True,
                                choices=[(x, x)
                                         for x in pytz.common_timezones],
                                default='Asia/Manila')

    class Meta:
        db_table = 'pcari_user_profile'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-id']

    def __str__(self):
        return self.user

    def display_name(self):
        if self.user.get_short_name():
            return self.user.get_short_name()
        else:
            return self.user.username

    @staticmethod
    def new_user_hook(sender, instance, created, **kwargs):
        if created:
            admin = UserProfile.objects.create(user=instance)
            admin.save()

            contact, created_contact = Contact.objects.get_or_create(
                imsi=settings.PCARI['ADMIN_IMSI'],
                callerid=settings.PCARI['ADMIN_CALLERID'])
            if created_contact:
                # contact.callerid = settings.PCARI['ADMIN_CALLERID']
                contact_profile, created_contact = ContactProfile.objects.get_or_create(
                    uuid=00000, firstname='ADMIN', lastname='PCARI', nickname='pcari', )
                ContactSimcards.objects.get_or_create(
                    contact_profile=contact_profile,
                    contact=contact
                )

            admin.contact = contact
            admin.save()


post_save.connect(UserProfile.new_user_hook, sender=User)


class Circle(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=500, blank=False, null=False)
    owner = models.ForeignKey(User, related_name='circle_owner')
    users = models.ManyToManyField(Contact, through='CircleUsers')

    class Meta:
        managed = True
        db_table = 'pcari_circles'
        verbose_name = 'Circle'
        verbose_name_plural = 'Circles'
        ordering = ['-id']

    def __unicode__(self):
        return self.name


class CircleUsers(models.Model):
    circle = models.ForeignKey(Circle)
    user = models.ForeignKey(Contact)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'pcari_circle_users'
        verbose_name = 'Circle Member'
        verbose_name_plural = 'Circle Members'
        ordering = ['-id']


class Document(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=80,
        blank=False,
        null=False,
        unique=True)
    description = models.CharField(max_length=500, blank=False, null=False)
    docfile = models.FileField(upload_to='documents')

    class Meta:
        db_table = 'pcari_documents'
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-id']

    def __unicode__(self):
        return '%s' % self.docfile.name


class Group(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80)
    owner = models.ForeignKey(Contact, related_name='group_owner')
    members = models.ManyToManyField(Contact, through='GroupMembers')
    last_modified = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'owner')
        managed = True
        db_table = 'pcari_groups'
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        ordering = ['-id']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('groups:group_update', kwargs={'pk': self.pk})


class GroupMembers(models.Model):
    group = models.ForeignKey(Group)
    user = models.ForeignKey(Contact)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'pcari_group_users'
        verbose_name = 'Group Member'
        verbose_name_plural = 'Group Members'
        ordering = ['-id']


REPORT_STATUS_CHOICES = (
    ('P', 'Published'),
    ('U', 'Unpublished')
)


class Report(models.Model):
    alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$',
                                  'Only alphanumeric characters are allowed.')

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    keyword = models.CharField(max_length=10, blank=False, null=False,
                               unique=True, validators=[alphanumeric])
    number = models.IntegerField(blank=False, null=False)
    status = models.CharField(max_length=1, blank=True, null=True,
                              choices=REPORT_STATUS_CHOICES,
                              default=REPORT_STATUS_CHOICES[1][0])
    chatplan = models.CharField(max_length=300, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    published_date = models.DateField(blank=True, null=True)
    author = models.ForeignKey(User, related_name='report_author')
    managers = models.ManyToManyField(Contact, through='ReportManagers')

    class Meta:
        db_table = 'pcari_reports'
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-id']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Report, self).save(*args, **kwargs)


class ReportManagers(models.Model):
    report = models.ForeignKey(Report)
    manager = models.ForeignKey(Contact)
    date_assigned = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'pcari_report_managers'
        verbose_name = 'Report Manager'
        verbose_name_plural = 'Report Managers'
        ordering = ['-id']


class ReportMessages(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(Contact)
    report = models.ForeignKey(Report)
    message = models.TextField(max_length=150)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'pcari_report_messages'
        verbose_name = 'Report Message'
        verbose_name_plural = 'Report Messages'
        ordering = ['-id']

    def __unicode__(self):
        return self.message


PUBLISHED_STATUS_CHOICES = (
    ('D', 'Downloaded'),
    ('I', 'Installed'),
)


class Script(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, blank=False, null=False)
    author = models.CharField(max_length=255, blank=False, null=False)
    version = models.CharField(max_length=10, blank=False, null=False)
    description = models.TextField(blank=True)
    package_name = models.CharField(max_length=500, blank=False, null=True)
    date_downloaded = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, blank=False, null=True,
                              choices=PUBLISHED_STATUS_CHOICES,
                              default=PUBLISHED_STATUS_CHOICES[0][0])
    chatplan = models.CharField(max_length=500, blank=False, null=True)
    fs_script = models.CharField(max_length=500, blank=False, null=False)
    arguments = JSONField(
        load_kwargs={'object_pairs_hook': collections.OrderedDict}, blank=True,
        null=True)

    class Meta:
        db_table = 'pcari_scripts'
        verbose_name = 'Script'
        verbose_name_plural = 'Scripts'
        ordering = ['-id']

    def __unicode__(self):
        return self.fs_script

    def get_plugin_name(self):
        return self.name


SERVICE_STATUS_CHOICES = (
    ('P', 'Published'),
    ('U', 'Unpublished')
)

SERVICE_TYPE_CHOICES = (
    ('P', 'Push Message'),
    ('I', 'Info Request')
)


class Service(models.Model):
    alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$',
                                  'Only alphanumeric characters are allowed.')

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    keyword = models.CharField(max_length=10, blank=False, null=False,
                               unique=True, validators=[alphanumeric])
    number = models.IntegerField(blank=False, null=False)
    status = models.CharField(max_length=1, blank=True, null=True,
                              choices=SERVICE_STATUS_CHOICES,
                              default=SERVICE_STATUS_CHOICES[1][0])
    published_date = models.DateField(blank=True, null=True)
    author = models.ForeignKey(User, related_name='service_author')
    script = models.ForeignKey(Script, db_column='script')
    script_arguments = JSONField(
        load_kwargs={'object_pairs_hook': collections.OrderedDict})
    chatplan = models.CharField(max_length=500, blank=True, null=True)
    source_file = models.FileField(upload_to='datasets/',
                                   blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    subscribers = models.ManyToManyField(Contact, through='ServiceSubscribers',
                                         related_name='subscribers')
    managers = models.ManyToManyField(Contact, through='ServiceManagers')
    service_type = models.CharField(max_length=1, blank=False, null=False,
                                    choices=SERVICE_TYPE_CHOICES,
                                    default=SERVICE_TYPE_CHOICES[1][0])

    class Meta:
        db_table = 'pcari_services'
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['-id']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('services:service_update', kwargs={'pk': self.pk})


class ServiceScheduledTasks(models.Model):
    service = models.ForeignKey(Service)
    periodic_task = models.ForeignKey(PeriodicTask)

    def stop(self):
        """pauses the task"""
        ptask = self.periodic_task
        ptask.enabled = False
        ptask.save()

    def start(self):
        """starts the task"""
        ptask = self.periodic_task
        ptask.enabled = True
        ptask.save()

    def terminate(self):
        self.stop()
        ptask = self.periodic_task
        self.delete()
        ptask.delete()

    def edit(self, period, every, args=None, kwargs=None):
        ptask = self.periodic_task
        interval_schedule = manage_interval(period, every)
        ptask.interval = interval_schedule
        if args:
            ptask.args = args
        if kwargs:
            ptask.kwargs = kwargs
        ptask.save()

    def get_interval(self):
        interval = PeriodicTask.objects.get(pk=self.periodic_task.pk).interval
        return IntervalSchedule.objects.get(pk=interval.pk)

    class Meta:
        managed = True
        db_table = 'pcari_service_scheduled_tasks'
        verbose_name = 'Service Scheduled Task'
        verbose_name_plural = 'Service Scheduled Tasks'
        ordering = ['-id']


class ServiceEvents(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    service = models.ForeignKey(Service)
    subscriber = models.ForeignKey(Contact)
    event = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'pcari_service_events'
        verbose_name = 'Service Event'
        verbose_name_plural = 'Service Events'
        ordering = ['-id']


class ServiceSubscribers(models.Model):
    service = models.ForeignKey(Service)
    subscriber = models.ForeignKey(Contact)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('service', 'subscriber')
        managed = True
        db_table = 'pcari_service_users'
        verbose_name = 'Service Subscriber'
        verbose_name_plural = 'Service Subscribers'
        ordering = ['-id']


class ServiceManagers(models.Model):
    service = models.ForeignKey(Service)
    manager = models.ForeignKey(Contact)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'pcari_service_managers'
        verbose_name = 'Service Manager'
        verbose_name_plural = 'Service Managers'
        ordering = ['-id']


class ServiceMessages(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(Contact)
    service = models.ForeignKey(Service)
    message = models.TextField(max_length=150)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'pcari_service_messages'
        verbose_name = 'Service Message'
        verbose_name_plural = 'Service Messages'
        ordering = ['-id']

    def __unicode__(self):
        return self.message


class Message(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(Contact)
    recipients = models.ManyToManyField(Contact,
                                        related_name='message_recipients',
                                        through='MessageRecipients')
    message = models.TextField(max_length=150)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'pcari_messages'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-id']

    def __unicode__(self):
        return self.message


class MessageRecipients(models.Model):
    message = models.ForeignKey(Message)
    user = models.ForeignKey(Contact)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'pcari_message_recipients'
        verbose_name = 'Message Recipient'
        verbose_name_plural = 'Message Recipients'
        ordering = ['-id']


PROMO_TYPE_CHOICES = (
    ('U', 'Unlimited'),
    ('B', 'Bulk'),
    ('D', 'Discounted'),
    ('G', 'Group Discount'),
)


class Promo(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(User)
    date_created = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=128, blank=False,
                            null=False, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    promo_type = models.CharField(max_length=1,
                                  blank=False,
                                  null=True,
                                  choices=PROMO_TYPE_CHOICES,
                                  default=PROMO_TYPE_CHOICES[0][0])
    # NOTE: subscribers field is PromoSubscription model link.
    # Do not touch this field
    subscribers = models.ManyToManyField(Contact,
                                         related_name='promo_subscription',
                                         through='PromoSubscription')
    keyword = models.CharField(max_length=10, blank=False,
                               null=False, unique=True)
    number = models.PositiveIntegerField(blank=False, null=False, default=555)

    # TODO: The promo model needs to be redesigned to accommodate multi-tiered
    # pricing. The current scheme just extended it to accommodate a new tier
    # and is not scalable in the long run

    # if promo_type is DISCOUNTED, we store the discounted price in millicents
    local_sms = models.PositiveIntegerField(default=0)
    local_call = models.PositiveIntegerField(default=0)
    globe_sms = models.PositiveIntegerField(default=0)
    globe_call = models.PositiveIntegerField(default=0)
    outside_sms = models.PositiveIntegerField(default=0)
    outside_call = models.PositiveIntegerField(default=0)

    # 1-day validity
    validity = models.PositiveIntegerField(default=1, null=False)

    class Meta:
        managed = True
        db_table = 'pcari_promos'
        verbose_name = 'Promo'
        verbose_name_plural = 'Promos'
        ordering = ['-id']

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.keyword)


class PromoSubscription(models.Model):
    promo = models.ForeignKey(Promo)
    contact = models.ForeignKey(Contact)

    date_availed = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField(null=True, blank=True)

    # TODO: The promo model needs to be redesigned to accommodate multi-tiered
    # pricing. The current scheme just extended it to accommodate a new tier
    # and is not scalable in the long run
    local_sms = models.PositiveIntegerField(default=0)
    local_call = models.PositiveIntegerField(default=0)
    globe_sms = models.PositiveIntegerField(default=0)
    globe_call = models.PositiveIntegerField(default=0)
    outside_sms = models.PositiveIntegerField(default=0)
    outside_call = models.PositiveIntegerField(default=0)

    class Meta:
        managed = True
        db_table = 'pcari_promo_subscription'
        verbose_name = 'Promo Subscriber'
        verbose_name_plural = 'Promo Subscribers'
        ordering = ['-id']


class Config(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=50, blank=False, null=False, unique=True)
    value = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'pcari_config'
        verbose_name = 'Config'
        verbose_name_plural = 'Configs'
        ordering = ['-id']


class Ivr(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=50,
        blank=False,
        null=False,
        unique=True)
    number = models.PositiveIntegerField(blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    xml_code = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'pcari_ivr'
        verbose_name = 'IVR'
        verbose_name_plural = 'IVRs'
        ordering = ['-id']
