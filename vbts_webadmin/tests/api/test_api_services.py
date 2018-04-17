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
from vbts_webadmin.utils import float_to_mc


class BaseClass(TestCase):
    """
        Base class for service API testing
    """

    def subscribe_to_service(self, imsi, keyword, balance):
        endaga_sub.get_numbers_from_imsi = Mock(return_value='123455')
        endaga_sub.get_account_balance = Mock(return_value=balance)
        endaga_sub.subtract_credit = Mock(return_value=None)
        send_sms.delay = Mock(return_value=None)

        url = '/api/service/subscribe'
        data = {
            'imsi': imsi,
            'keyword': keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data

    def unsubscribe_to_service(self, imsi, keyword):
        endaga_sub.get_numbers_from_imsi = Mock(return_value='123455')
        send_sms.delay = Mock(return_value=None)

        url = '/api/service/unsubscribe'
        data = {
            'imsi': imsi,
            'keyword': keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data

    def send_subscriber_msg(self, imsi, keyword, message):
        endaga_sub.get_numbers_from_imsi = Mock(return_value='123455')
        send_sms.delay = Mock(return_value=None)

        url = '/api/service/send'
        data = {
            'imsi': imsi,
            'keyword': keyword,
            'message': message
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data

    def get_service_status(self, imsi, keyword):
        endaga_sub.get_numbers_from_imsi = Mock(return_value='123455')
        send_sms.delay = Mock(return_value=None)

        url = '/api/service/status'
        data = {
            'imsi': imsi,
            'keyword': keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data

    def get_service_price(self, keyword):
        url = '/api/service/price'
        data = {
            'keyword': keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data

    def create_event(self, imsi, keyword):
        url = '/api/service/event'
        data = {
            'imsi': imsi,
            'keyword': keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data


class ServiceAPITest(BaseClass):
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
        cls.balance = float_to_mc(10)
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        # create another subscriber
        cls.imsi2 = 'IMSI001010000008888'
        cls.callerid2 = '639991110000'
        cls.balance2 = float_to_mc(10)
        cls.subscriber2 = models.Contact(imsi=cls.imsi2,
                                         callerid=cls.callerid2)
        cls.subscriber2.save()

        cls.script = models.Script(name='Sample Script',
                                   author='Some One',
                                   version='0.0.1',
                                   package_name='sample name',
                                   fs_script='PCARI_dictionary.py',
                                   chatplan='dictionary.xml',
                                   status='D',
                                   arguments='{"arg": 11}')
        cls.script.save()

        cls.keyword = 'KEY'
        cls.price = float_to_mc(5)
        cls.service = models.Service(name='Sample Service',
                                     keyword=cls.keyword,
                                     number='111',
                                     author=cls.admin,
                                     script=cls.script,
                                     status='P',
                                     service_type='P',
                                     price=cls.price
                                     )
        models.Service.create_or_update_chatplan = Mock(return_value=None)
        cls.service.save()

        cls.manager = models.ServiceManagers(service=cls.service,
                                             manager=cls.admincontact)
        cls.manager.save()

        cls.subscription = models.ServiceSubscribers(
            service=cls.service, subscriber=cls.subscriber2)

        cls.subscription.save()

    @classmethod
    def tearDownClass(cls):
        cls.admin.delete()
        cls.subscriber.delete()
        cls.subscriber2.delete()
        cls.service.delete()
        cls.manager.delete()
        cls.script.delete()

    def test_subscribe_to_service(self):
        """ We should be able to subscribe to a service """
        codes, data = self.subscribe_to_service(self.imsi, self.keyword,
                                                self.balance)
        self.assertEqual(codes, 200)
        self.assertEqual(data, 'OK SUBSCRIBED')

    def test_subscribe_to_service_invalid_keyword(self):
        """ The service keyword should be valid """
        codes, data = self.subscribe_to_service(self.imsi, 'INVALID',
                                                self.balance)
        self.assertEqual(codes, 400)
        self.assertEqual(data, 'ERROR: Invalid keyword.')

    def test_subscribe_to_service_unpublished(self):
        """ The service should be published """
        self.service.status = 'U'
        self.service.save()
        codes, data = self.subscribe_to_service(self.imsi, self.keyword,
                                                self.balance)
        self.assertEqual(codes, 400)
        self.assertEqual(data, 'ERROR: Invalid keyword.')

    def test_subscribe_twice(self):
        """ We should get a friendly msg if we are already subscribed
            The system should not create a new entry in ServiceSubscribers
        """
        self.assertEqual(1, models.ServiceSubscribers.objects.all().count())
        codes, data = self.subscribe_to_service(self.imsi2,
                                                self.keyword,
                                                self.balance)
        self.assertEqual(codes, 200)
        self.assertEqual(data, 'OK ALREADY SUBSCRIBED')
        # number of entries should still be the same
        self.assertEqual(1, models.ServiceSubscribers.objects.all().count())

    def test_unsubscribe_to_service(self):
        """ We should be able to opt out from a service """
        self.assertEqual(1, models.ServiceSubscribers.objects.all().count())
        codes, data = self.unsubscribe_to_service(self.imsi2, self.keyword)
        self.assertEqual(codes, 200)
        self.assertEqual(data, 'OK UNSUBSCRIBED')
        self.assertEqual(0, models.ServiceSubscribers.objects.all().count())

    def test_unsubscribe_to_service_invalid_keyword(self):
        """ You have to put a valid keyword """
        codes, data = self.unsubscribe_to_service(self.imsi, 'INVALID')
        self.assertEqual(codes, 400)
        self.assertEqual(data, "ERROR: You are not currently subscribed to "
                               "the %s service." % 'INVALID')

    def test_unsubscribe_but_no_valid_subscription(self):
        """ You can't unsubscribe if you are not registered
            in the first place
        """
        codes, data = self.unsubscribe_to_service(self.imsi, self.keyword)
        self.assertEqual(codes, 400)
        self.assertEqual(data,
                         "ERROR: You are not currently subscribed to "
                         "the %s service." % self.keyword)

    def test_send_subscriber_msg(self):
        """ The service manager must be able to send a message to end users
            who availed of a particular service.
        """
        msg = 'Hello, this is a sample message.'
        codes, data = self.send_subscriber_msg(self.manager.manager.imsi,
                                               self.keyword, msg)
        self.assertEqual(codes, 200)
        self.assertEqual(data, 'ANNOUNCEMENT SENT')

    def test_send_subscriber_msg_not_manager(self):
        """ You wont be able to send if you're not the service manager """
        msg = 'Hello, this is a sample message.'
        codes, data = self.send_subscriber_msg(self.imsi,
                                               self.keyword, msg)
        self.assertEqual(codes, 400)
        self.assertEqual(data, "ERROR: No administrative privileges to send to"
                               " this %s's subscribers." % self.keyword)

    def test_send_subscriber_msg_invalid_keyword(self):
        """ You wont be able to send if we have an invalid keyword """
        msg = 'Hello, this is a sample message.'
        codes, data = self.send_subscriber_msg(self.imsi,
                                               'INVALID', msg)
        self.assertEqual(codes, 400)
        self.assertEqual(data, "ERROR: Invalid service.")

    def test_send_subscriber_msg_unpublished_service(self):
        """ We can only send to published services """
        msg = 'Hello, this is a sample message.'
        self.service.status = 'U'
        self.service.save()
        codes, data = self.send_subscriber_msg(self.manager.manager.imsi,
                                               self.keyword, msg)
        self.assertEqual(codes, 400)
        self.assertEqual(data, "ERROR: Invalid service.")

    def test_normal_get_status_subscribed(self):
        codes, data = self.get_service_status(self.imsi2, self.keyword)
        self.assertEqual(codes, 200)
        self.assertEqual(data, 'OK STATUS - SUBSCRIBED')

    def test_get_status_not_subscribed(self):
        codes, data = self.get_service_status(self.imsi, self.keyword)
        self.assertEqual(codes, 200)
        self.assertEqual(data, 'OK STATUS - NOT SUBSCRIBED')

    def test_status_invalid_keyword(self):
        codes, data = self.get_service_status(self.imsi, 'INVALID KEYWORD')
        self.assertEqual(codes, 400)
        self.assertEqual(data, 'ERROR: Invalid keyword.')

    def test_imsi_not_in_vbts_table(self):
        """
            We cannot do service API actions
            if we are not registered to the VBTS databse.
        """
        endaga_sub.get_numbers_from_imsi = Mock(return_value='639999')
        code, data = self.subscribe_to_service('IMSI077711119988',
                                               self.keyword,
                                               self.balance)
        self.assertEqual(code, 400)
        self.assertEqual(data, 'ERROR: Not registered subscriber.')

        code, data = self.unsubscribe_to_service('IMSI077711119988',
                                                 self.keyword)
        self.assertEqual(code, 400)
        self.assertEqual(data, 'ERROR: Not registered subscriber.')

        code, data = self.get_service_status('IMSI077711119988',
                                             self.keyword)
        self.assertEqual(code, 404)
        self.assertEqual(data, 'ERROR: Not registered subscriber.')

    def test_unsubscribe_bad_args(self):
        """ Requests with bad arguments should fail """
        endaga_sub.get_numbers_from_imsi = Mock(return_value='123455')
        send_sms.delay = Mock(return_value=None)

        urls = ['/api/service/unsubscribe',
                '/api/service/subscribe',
                '/api/service/status',
                '/api/service/price',
                '/api/service/event']

        for url in urls:
            data = {
                'imsI': self.imsi,  # make the args bad
                'keyW0rd': self.keyword
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data, 'ERROR: Missing arguments.')

    def test_normal_get_service_price(self):
        code, data = self.get_service_price(self.keyword)
        self.assertEqual(code, 200)
        self.assertEqual(data, self.price)

    def test_get_service_price_invalid_keyword(self):
        code, data = self.get_service_price('INVALID KEYWORD')
        self.assertEqual(code, 200)
        self.assertEqual(data, 0)

    def test_subscribe_to_service_insufficient_balance(self):
        self.assertEqual(1, models.ServiceSubscribers.objects.all().count())
        codes, data = self.subscribe_to_service(self.imsi,
                                                self.keyword,
                                                float_to_mc(1))
        self.assertEqual(codes, 402)
        self.assertEqual(data, 'Insufficient balance')
        self.assertEqual(1, models.ServiceSubscribers.objects.all().count())

    def test_subscribe_to_service_zero_balance(self):
        self.assertEqual(1, models.ServiceSubscribers.objects.all().count())
        codes, data = self.subscribe_to_service(self.imsi,
                                                self.keyword,
                                                float_to_mc(0))
        self.assertEqual(codes, 402)
        self.assertEqual(data, 'Insufficient balance')
        self.assertEqual(1, models.ServiceSubscribers.objects.all().count())

    def test_normal_create_event(self):
        self.assertEqual(0, models.ServiceEvents.objects.all().count())
        codes, data = self.create_event(self.imsi2, self.keyword)
        self.assertEqual(codes, 200)
        self.assertEqual(data, 'OK EVENT')
        self.assertEqual(1, models.ServiceEvents.objects.all().count())

    def test_create_event_invalid_keyword(self):
        self.assertEqual(0, models.ServiceEvents.objects.all().count())
        codes, data = self.create_event(self.imsi2, 'INVALID KEYWORD')
        self.assertEqual(codes, 400)
        self.assertEqual(data, 'BAD ARGS')
        self.assertEqual(0, models.ServiceEvents.objects.all().count())

    def test_create_event_invalid_imsi(self):
        self.assertEqual(0, models.ServiceEvents.objects.all().count())
        codes, data = self.create_event('inavlid imsi', self.keyword)
        self.assertEqual(codes, 400)
        self.assertEqual(data, 'BAD ARGS')
        self.assertEqual(0, models.ServiceEvents.objects.all().count())
