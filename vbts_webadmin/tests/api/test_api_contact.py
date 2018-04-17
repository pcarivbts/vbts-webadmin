"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.test import TestCase
from mock import Mock

from vbts_webadmin import models
from vbts_webadmin.tasks import send_sms


class ContactApiTest(TestCase):

    """
        Base class for contact API testing
    """

    @classmethod
    def setUpClass(cls):
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

    @classmethod
    def tearDownClass(cls):
        models.Contact.objects.all().delete()

    def test_register(self):
        """ We should be able to register """

        self.assertEqual(1, models.Contact.objects.all().count())
        send_sms.delay = Mock(return_value=None)

        url = '/api/contact/create'
        data = {
            'imsi': 'IMSI00101001010101',
            'callerid': '639212012901'
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual(200, response.status_code)
        self.assertEqual('OK CREATED', response.data)
        self.assertEqual(2, models.Contact.objects.all().count())

    def test_register_twice(self):
        """ We can register twice. It's as if we are updating the entry """
        self.assertEqual(1, models.Contact.objects.all().count())
        send_sms.delay = Mock(return_value=None)

        url = '/api/contact/create'
        data = {
            'imsi': 'IMSI001010000009999',
            'callerid': '639991111111'
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual('OK CREATED', response.data)
        self.assertEqual(1, models.Contact.objects.all().count())

    def test_register_bad_args_1(self):
        """ Requests with bad arguments will fail """
        # Contacts table should contain 1 entry at the start
        self.assertEqual(1, models.Contact.objects.all().count())
        send_sms.delay = Mock(return_value=None)

        url = '/api/contact/create'
        data = {
            'imsi': 'IMSI00101001010101',
            # missing callerid
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual(400, response.status_code)
        self.assertEqual('ERROR', response.data)
        # Contact count should still be the same
        self.assertEqual(1, models.Contact.objects.all().count())

    def test_register_bad_args_2(self):
        """ Requests with bad arguments will fail """
        # Contacts table should contain 1 entry at the start
        self.assertEqual(1, models.Contact.objects.all().count())
        send_sms.delay = Mock(return_value=None)

        url = '/api/contact/create'
        data = {
            # missing imsi
            'callerid': '639991111111'
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual(400, response.status_code)
        self.assertEqual('ERROR', response.data)
        # Contact count should still be the same
        self.assertEqual(1, models.Contact.objects.all().count())

    def test_register_bad_args_3(self):
        """ Requests with bad arguments will fail """
        # Contacts table should contain 1 entry at the start
        self.assertEqual(1, models.Contact.objects.all().count())
        send_sms.delay = Mock(return_value=None)

        url = '/api/contact/create'
        data = {
            'imsI': 'IMSI00101001010101',
            'caLLerid': '639991111111'
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual(400, response.status_code)
        self.assertEqual('ERROR', response.data)
        # Contact count should still be the same
        self.assertEqual(1, models.Contact.objects.all().count())
