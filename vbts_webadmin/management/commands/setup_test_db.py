"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.

Sets up a a basic test DB for external (non-test suite) testing.

Adds Admin, Circles, Groups, Services, Subscribers -- all this should then
be visible in a local dashboard.  Make sure you've first properly
setup the db and its migrations.  Then you can login with the test
username and pw as defined below.

Usage:
    python manage.py setup_test_db

To reset the local test db:
    python manage.py flush
    python manage.py migrate vbts_webadmin
    python manage.py migrate authtoken
"""

import datetime
import random
import sys
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db.models import Q
from faker import Factory

from vbts_subscribers.models import SipBuddies
from vbts_webadmin.models import Circle
from vbts_webadmin.models import Contact
from vbts_webadmin.models import Group
from vbts_webadmin.models import GroupMembers
from vbts_webadmin.models import CircleUsers
from vbts_webadmin.models import UserProfile


class Command(BaseCommand):

    """A custom management command.

    As per the docs:
    docs.djangoproject.com/en/1.7/howto/custom-management-commands/
    """

    help = 'sets up a test db -- see management/commands for more'

    def create_birthdate(self):
        year = random.randint(1950, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        birthdate = datetime(year, month, day)
        return birthdate

    def create_contacts(self, block_size=30):
        buddies = SipBuddies.objects.all()[:block_size]
        # Add contacts
        fake = Factory.create('it_ES')
        for buddy in buddies:
            imsi = buddy.name
            callerid = buddy.callerid
            fname = fake.first_name()
            lname = fake.last_name()
            birthdate = self.create_birthdate()
            address = fake.address
            contact = Contact(imsi=imsi, callerid=callerid,
                              firstname=fname, lastname=lname,
                              birthdate=birthdate, address=address)
            contact.save()

    def create_groups(self, group_size=5):
        sys.stdout.write('creating groups ..\n')
        owners = Contact.objects.all().order_by('?')[:group_size]
        for owner in owners:
            name = "Group %s" % owner.firstname.upper
            group = Group(name=name, owner=owner)
            members = Contact.objects.filter(
                ~Q(imsi=owner.imsi)).order_by('?')[:3]
            group.save()
            for member in members:
                member = GroupMembers.objects.create(
                    user=member, group=group)
                member.save()

    def create_circles(self, group_size=5):
        sys.stdout.write('creating circles ..\n')
        fake = Factory.create('it_IT')

        for _ in (0, group_size):
            circle = Circle(name=fake.last_name())
            circle.owner = User.objects.filter(~Q(username='pcarivbts'))[0]
            circle.save()

            members = Contact.objects.all().order_by('?')[:4]
            for member in members:
                member = CircleUsers.objects.create(user=member, circle=circle)
                member.save()

    def create_userprofile(self, username, password):
        # Add one user with several activities.
        sys.stdout.write('creating user: %s %s ..\n' % (username, password))
        user = User(username=username, email="%s@pcarivbts.com.ph" % username)
        user.set_password(password)
        user.save()

        # Get user profile and add some credit.
        sys.stdout.write('setting user profile ..\n')
        user_profile = UserProfile(user=user)
        contact = Contact(imsi='IMSI00000000000', callerid='0000',
                          firstname='PCARI-VBTS', lastname='ADMIN')
        user_profile.contact = contact
        user_profile.save()

        # Add one user with no such activity.
        username = 'newuser'
        sys.stdout.write('creating user "%s"..\n' % username)
        user = User(username=username, email="%s@pcarivbts.com.ph" % username)
        user.set_password('newpw')
        user.save()

    def create_default_services(self):
        # Add default  services
        sys.stdout.write('creating scripts and services: %s %s ..\n' %
                         (username, password))

    def handle(self, *args, **options):
        self.create_userprofile()
        self.create_contacts()
        self.create_groups()
        self.create_circles()
        self.create_default_services()
