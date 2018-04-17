"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from core.subscriber import subscriber as endaga_sub
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from mock import Mock

from vbts_webadmin import models
from vbts_webadmin.tasks import send_sms

from unittest import skip


class BaseClass(TestCase):
    """
        Base class for Report API testing
    """

    def submit_report(self, imsi, keyword, message):
        endaga_sub.get_numbers_from_imsi = Mock(return_value='123455')
        send_sms.delay = Mock(return_value=None)

        url = '/api/report/submit'
        data = {
            'imsi': imsi,
            'keyword': keyword,
            'message': message
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data


class ReportAPITest(BaseClass):
    @classmethod
    def setUpClass(cls):
        # create dummy admin
        cls.admin = User(username='XX', email='XX@user.com')
        cls.admin.save()

        # Fetch auto-created Contact for admin
        cls.admincontact = models.Contact.objects.get(
            imsi=settings.PCARI['ADMIN_IMSI'])

        # create test subscriber
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.keyword = 'KEY'
        cls.report = models.Report(name='Sample Report',
                                   keyword=cls.keyword,
                                   number='111',
                                   author=cls.admin,
                                   chatplan='sample.xml',
                                   status='P',
                                   )
        models.Report.create_or_update_chatplan = Mock(return_value=None)
        cls.report.save()

        cls.manager = models.ReportManagers(report=cls.report,
                                            manager=cls.admincontact)
        cls.manager.save()

    @classmethod
    def tearDownClass(cls):
        cls.admin.delete()
        cls.subscriber.delete()
        cls.report.delete()
        cls.manager.delete()

    def test_normal_submit_report(self):
        """ We should be to submit a report """
        msg = 'Hello, this is a sample message.'
        codes, data = self.submit_report(self.imsi, self.keyword, msg)
        print (self.report.keyword)
        print (self.keyword)
        self.assertEqual(codes, 200)
        self.assertEqual(data, 'OK CREATED')

    def test_invalid_keyword(self):
        msg = 'Hello, this is a sample message.'
        codes, data = self.submit_report(self.imsi, 'INVALID', msg)
        self.assertEqual(codes, 400)
        self.assertEqual(data, 'ERROR: Invalid keyword.')

    def test_invalid_imsi(self):
        msg = 'Hello, this is a sample message.'
        codes, data = self.submit_report('IMSIinvalid', self.keyword, msg)
        self.assertEqual(codes, 400)
        self.assertEqual(data, 'ERROR: Not registered subscriber.')
