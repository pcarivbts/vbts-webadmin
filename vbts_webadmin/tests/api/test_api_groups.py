"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import random

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from mock import Mock

from vbts_webadmin import models
from vbts_webadmin.tasks import send_sms


class GroupBaseClass(TestCase):

    """
        Base class for Groups API testing
    """

    def create_group(self, imsi, name, mems):
        send_sms.delay = Mock(return_value=None)

        url = '/api/group/create'
        data = {
            'imsi': imsi,
            'name': name,
            'mems': mems
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data

    def delete_group(self, imsi, name):
        send_sms.delay = Mock(return_value=None)

        url = '/api/group/delete'
        data = {
            'imsi': imsi,
            'name': name,
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data

    def message_group(self, imsi, name, msg):
        send_sms.delay = Mock(return_value=None)

        url = '/api/group/send'
        data = {
            'imsi': imsi,
            'name': name,
            'msg': msg
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data


class GroupApiTest(GroupBaseClass):

    @classmethod
    def setUpClass(cls):
        cls.key = models.Config(key='max_groups_per_subscriber', value='NA')
        cls.key.save()

        # create dummy admin
        cls.admin = User(username='yy.xxx', email='xy@xy.com')
        cls.admin.save()

        # create dummy subscribers
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.imsi1 = 'IMSI001010000009990'
        cls.callerid1 = '639991111112'
        cls.subscriber1 = models.Contact(imsi=cls.imsi1,
                                         callerid=cls.callerid1)

        cls.subscriber1.save()

        cls.imsi2 = 'IMSI001010000009991'
        cls.callerid2 = '639991111113'
        cls.subscriber2 = models.Contact(imsi=cls.imsi2,
                                         callerid=cls.callerid2)
        cls.subscriber2.save()

        # Create a dummy group and group members
        # From FS, we are passing in group name in uppercase
        cls.groupname = 'dummy_group'.upper()
        cls.dummygroup = models.Group(name=cls.groupname,
                                      owner=cls.subscriber)
        cls.dummygroup.save()

        cls.gm1 = models.GroupMembers(group=cls.dummygroup,
                                      user=cls.subscriber1,
                                      date_joined=timezone.now())
        cls.gm1.save()

    @classmethod
    def tearDownClass(cls):
        cls.key.delete()
        cls.subscriber.delete()
        cls.subscriber1.delete()
        cls.subscriber2.delete()
        cls.dummygroup.delete()
        cls.gm1.delete()

    def test_create_group(self):
        """ We can create a new group"""
        self.assertEqual(1, models.Group.objects.all().count())
        code, data = self.create_group(self.imsi, 'new_group',
                                       self.callerid1 + ',' + self.callerid2)
        self.assertEqual(200, code)
        self.assertEqual('OK CREATED', data)
        self.assertEqual(2, models.Group.objects.all().count())

    def test_create_group_uncanonical_mems_callerid(self):
        """ We accept uncanonicalized numbers to create a group """
        callerid1 = '09991111112'
        callerid2 = '09991111113'
        self.assertEqual(1, models.Group.objects.all().count())
        code, data = self.create_group(self.imsi, 'new_group',
                                       callerid1 + ',' + callerid2)
        self.assertEqual(200, code)
        self.assertEqual('OK CREATED', data)
        self.assertEqual(2, models.Group.objects.all().count())

    def test_create_group_mixed_number_formats(self):
        """ We accept both canonicalized and uncanonicalized numbers
            to create a group
        """
        callerid1 = '09991111112'
        self.assertEqual(1, models.Group.objects.all().count())
        code, data = self.create_group(self.imsi, 'new_group',
                                       callerid1 + ',' + self.callerid2)
        self.assertEqual(200, code)
        self.assertEqual('OK CREATED', data)
        self.assertEqual(2, models.Group.objects.all().count())

    def test_create_group_same_name_diff_imsi(self):
        """ We can create a group with same names as long as the IMSIs are
            different
        """
        self.assertEqual(1, models.Group.objects.all().count())
        code, data = self.create_group(self.imsi1, 'new_group',
                                       self.callerid1 + ',' + self.callerid2)
        self.assertEqual(200, code)
        self.assertEqual('OK CREATED', data)
        self.assertEqual(2, models.Group.objects.all().count())

    def test_create_group_duplicate_imsi_name(self):
        """ We cannot create a group with the same (imsi, name) """
        code, data = self.create_group(self.imsi, self.groupname,
                                       self.callerid1 + ',' + self.callerid2)
        self.assertEqual(400, code)
        self.assertEqual('Constraint Failed', data)

    def test_delete_group(self):
        """ We can delete an existing group"""
        self.assertEqual(1, models.Group.objects.all().count())
        code, data = self.delete_group(self.imsi, self.groupname)
        self.assertEqual(200, code)
        self.assertEqual('DELETE OK', data)
        self.assertEqual(0, models.Group.objects.all().count())

    def test_delete_non_existent_group(self):
        """ Deleting a non-existent group should fail """
        self.assertEqual(1, models.Group.objects.all().count())
        code, data = self.delete_group(self.imsi, 'echos group')
        self.assertEqual(400, code)
        self.assertEqual('DELETE FAIL', data)
        self.assertEqual(1, models.Group.objects.all().count())

    def test_delete_group_not_owned(self):
        """ We cannot delete a group if we do not own it """
        self.assertEqual(1, models.Group.objects.all().count())
        code, data = self.delete_group(self.imsi2, self.groupname)
        self.assertEqual(400, code)
        self.assertEqual('DELETE FAIL', data)
        self.assertEqual(1, models.Group.objects.all().count())

    def test_message_group_by_owner(self):
        """ An admin/group owner can send a message to the group members """
        code, data = self.message_group(self.imsi, self.groupname,
                                        'Hello there!')
        self.assertEqual(200, code)
        self.assertEqual('OK SEND', data)

    def test_message_group_by_member(self):
        """ An member can send a message to the group members """
        code, data = self.message_group(self.imsi1, self.groupname,
                                        'Hello there!')
        self.assertEqual(200, code)
        self.assertEqual('OK SEND', data)

    def test_message_group_by_non_member(self):
        """ A non-member cannot send a message to the group members """
        code, data = self.message_group(self.imsi2, self.groupname,
                                        'Hello there!')
        self.assertEqual(403, code)
        self.assertEqual('Forbidden', data)


class GroupApiLimitsTest(GroupBaseClass):

    @classmethod
    def setUpClass(cls):
        cls.limit = random.randint(1, 10)
        cls.key = models.Config(key='max_groups_per_subscriber',
                                value=str(cls.limit))
        cls.key.save()

        # create dummy admin
        cls.admin = User(username='User2', email='2@user.com')
        cls.admin.save()

        # create dummy subscribers
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.imsi1 = 'IMSI001010000009990'
        cls.callerid1 = '639991111112'
        cls.subscriber1 = models.Contact(imsi=cls.imsi1,
                                         callerid=cls.callerid1)

        cls.subscriber1.save()

        cls.imsi2 = 'IMSI001010000009991'
        cls.callerid2 = '639991111113'
        cls.subscriber2 = models.Contact(imsi=cls.imsi2,
                                         callerid=cls.callerid2)
        cls.subscriber2.save()

    @classmethod
    def tearDownClass(cls):
        cls.key.delete()
        cls.subscriber.delete()
        cls.subscriber1.delete()
        cls.subscriber2.delete()

    def test_create_group_exceed_limit(self):
        """ We cannot create new groups if we have reached the limit. """
        # we start with zero groups
        self.assertEqual(0, models.Group.objects.all().count())

        i = 0
        while i < self.limit:
            code, data = self.create_group(
                self.imsi, 'NEW_GROUP_' + str(i), self.callerid1 + ',' + self.callerid2)
            self.assertEqual(200, code)
            self.assertEqual('OK CREATED', data)
            # group count gets incremented
            i += 1
            self.assertEqual(i, models.Group.objects.all().count())

        # let's try to create again, this should exceed limit
        code, data = self.create_group(self.imsi, 'new_group_attempt',
                                       self.callerid1 + ',' + self.callerid2)
        self.assertEqual(403, code)
        self.assertEqual('Too many groups', data)
        # group count should be equal to defined limit
        self.assertEqual(self.limit, models.Group.objects.all().count())

    def test_create_group_unlimited(self):
        """ We can create unlimited groups. """
        # we change first our key to 'NA' (unlimited)
        self.key.value = 'NA'
        self.key.save()

        # we start with zero groups
        self.assertEqual(0, models.Group.objects.all().count())

        i = 0
        while i < self.limit:
            code, data = self.create_group(
                self.imsi, 'NEW_GROUP_' + str(i), self.callerid1 + ',' + self.callerid2)
            self.assertEqual(200, code)
            self.assertEqual('OK CREATED', data)
            # group count gets incremented
            i += 1
            self.assertEqual(i, models.Group.objects.all().count())

        # let's try to create again, we should be able to do so
        code, data = self.create_group(self.imsi, 'new_group_attempt',
                                       self.callerid1 + ',' + self.callerid2)
        self.assertEqual(200, code)
        self.assertEqual('OK CREATED', data)
        # group count should increment
        self.assertEqual(i + 1, models.Group.objects.all().count())
