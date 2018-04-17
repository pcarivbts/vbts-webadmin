"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import random
from datetime import timedelta

from core import billing
from core.subscriber import subscriber as endaga_sub
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from mock import Mock

from vbts_webadmin import models
from vbts_webadmin.tasks import purge_entry
from vbts_webadmin.tasks import send_sms
from vbts_webadmin.utils import float_to_mc
from core import events


class BaseClass(TestCase):

    """
        Base class for promo API testing
    """

    @classmethod
    def setUpClass(cls):
        # create our required configuration keys
        cls.key1 = models.Config(key='max_promo_call_duration', value='180')
        cls.key1.save()
        cls.key2 = models.Config(key='promo_limit_type', value='NA')
        cls.key2.save()
        cls.key3 = models.Config(key='max_promo_subscription', value='5')
        cls.key3.save()
        cls.key4 = models.Config(key='min_balance_required', value='5')
        cls.key4.save()

        # create dummy admin
        cls.admin = User(username='User', email='user@user.com')
        cls.admin.save()

    @classmethod
    def tearDownClass(cls):
        cls.key1.delete()
        cls.key2.delete()
        cls.key3.delete()
        cls.key4.delete()
        cls.admin.delete()

    def subscribe_to_promo(self, imsi, keyword, balance):
        endaga_sub.get_account_balance = Mock(return_value=balance)
        endaga_sub.subtract_credit = Mock(return_value=None)
        send_sms.delay = Mock(return_value=None)
        purge_entry.apply_async = Mock(return_value=None)
        events.create_sms_event = Mock(return_value=None)

        url = '/api/promo/subscribe'
        data = {
            'imsi': imsi,
            'keyword': keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data

    def unsubscribe_to_promo(self, imsi, keyword):
        endaga_sub.get_numbers_from_imsi = Mock(return_value='631111111')
        send_sms.delay = Mock(return_value=None)

        url = '/api/promo/unsubscribe'
        data = {
            'imsi': imsi,
            'keyword': keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        return response.status_code, response.data

    def get_service_type(self, reg_types, dest):
        status = []
        output = []
        for i in xrange(0, len(reg_types)):
            url = '/api/promo/getservicetype'
            data = {
                'trans': reg_types[i],
                'imsi': self.imsi,
                'dest': dest[i]
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(response.data)
        return status, output

    def get_required_minimum_balance(self, reg_types, tariff):
        status = []
        output = []
        for i in xrange(0, len(reg_types)):
            url = '/api/promo/getminbal'
            data = {
                'trans': reg_types[i],
                'tariff': tariff[i]
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(response.data)
        return status, output

    def get_service_tariff(self, reg_types, destination):
        status = []
        output = []
        for trans in reg_types:
            url = '/api/promo/getservicetariff'
            data = {
                'trans': trans,
                'imsi': self.imsi,
                'dest': destination
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(int(response.data))
        return status, output

    def get_sec_avail(self, reg_types, destination, balance):
        output = []
        status = []
        for trans in reg_types:
            url = '/api/promo/getsecavail'
            data = {
                'trans': trans,
                'imsi': self.imsi,
                'dest': destination,
                'balance': balance
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(int(float(response.data)))
        return status, output

    def quota_deduct(self, reg_types, amount):
        status = []
        output = []
        for i in xrange(0, len(reg_types)):
            url = '/api/promo/deduct'
            data = {
                'trans': reg_types[i],
                'imsi': self.imsi,
                'amount': amount[i]
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(response.data)
        return status, output


class NoPromoTest(BaseClass):

    """
        We test the case when the subscriber is not subscribed to any promo.
    """

    @classmethod
    def setUpClass(cls):
        super(NoPromoTest, cls).setUpClass()
        # create test subscriber
        cls.imsi = 'IMSI001010000009999'

    @classmethod
    def tearDownClass(cls):
        super(NoPromoTest, cls).tearDownClass()

    def test_get_service_type(self):
        """We should get the regular service types since we dont have promos"""
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     ]
        dest = ['63999999123', '63999999123',
                '1999999123', '1999999123'
                ]
        expected = reg_types
        codes, data = self.get_service_type(reg_types, dest)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_required_minimum_balance(self):
        """POST should always return the original tariff for regular types"""
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     'free_sms', 'free_call',
                     'error_sms', 'error_call'
                     ]
        tariff_data = []
        for i in reg_types:
            tariff_data.append(str(random.randint(0, 100)))
        codes, data = self.get_required_minimum_balance(reg_types, tariff_data)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], tariff_data[i])

    def test_get_service_tariff(self):
        """POST should always return the original tariff for regular types"""
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     'free_sms', 'free_call',
                     'error_sms', 'error_call'
                     ]
        expected = []
        destination = '123456789'
        for trans in reg_types:
            expected.append(billing.get_service_tariff(trans,
                                                       trans.split('_')[1],
                                                       destination))
        codes, data = self.get_service_tariff(reg_types, destination)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_sec_avail(self):
        """For regular call types, it depends on the available balance."""
        reg_types = ['local_call', 'outside_call',  # 'free_call',
                     ]
        expected = []
        destination = '12345678'
        balance = 10000000
        for trans in reg_types:
            expected.append(billing.get_seconds_available(int(balance),
                                                          trans,
                                                          destination))
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_sec_avail_with_no_balance(self):
        """ For discounted promo types, it depends on the available balance.
            For this case, since no balance, should return 0
        """
        reg_types = ['local_call', 'outside_call',
                     ]
        destination = '12345678'
        balance = 0
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 0)

    def test_get_service_type_bad_args(self):
        """We can't get service_types if we passed bad args"""
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     ]
        dest = ['63999999123', '63999999123',
                '1999999123', '1999999123'
                ]
        status = []
        output = []
        for i in xrange(0, len(reg_types)):
            url = '/api/promo/getservicetype'
            data = {
                'trANs': reg_types[i],  # make the args bad
                'imSi': self.imsi,
                'dest': dest[i]
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(response.data)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(status[i], 400)
            self.assertEqual(output[i], 'Missing Args')

    def test_get_required_minimum_balance_bad_args(self):
        """We can't get the required min balance if we passed bad args"""
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     'free_sms', 'free_call',
                     'error_sms', 'error_call'
                     ]
        tariff_data = []
        for i in reg_types:
            tariff_data.append(str(random.randint(0, 100)))
        status = []
        output = []
        for i in xrange(0, len(reg_types)):
            url = '/api/promo/getminbal'
            data = {
                'trANs': reg_types[i],  # make the args bad
                'tar!ff': tariff_data[i]
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(response.data)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(status[i], 400)
            self.assertEqual(output[i], 'Missing Args')

    def test_get_service_tariff_bad_args(self):
        """We can't get service_tariff if we passed bad args"""
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     'free_sms', 'free_call',
                     'error_sms', 'error_call'
                     ]
        expected = []
        destination = '123456789'
        for trans in reg_types:
            expected.append(billing.get_service_tariff(trans,
                                                       trans.split('_')[1],
                                                       destination))
        status = []
        output = []
        for trans in reg_types:
            url = '/api/promo/getservicetariff'
            data = {
                'trAns': trans,  # make the args bad
                'ims1': self.imsi,
                'dest': destination
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(response.data)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(status[i], 400)
            self.assertEqual(output[i], 'Missing Args')

    def test_get_sec_avail_bad_args(self):
        """We can't get sec_avail    if we passed bad args"""
        reg_types = ['local_call', 'outside_call',  # 'free_call',
                     ]
        expected = []
        destination = '12345678'
        balance = 10000000
        for trans in reg_types:
            expected.append(billing.get_seconds_available(int(balance),
                                                          trans,
                                                          destination))
        output = []
        status = []
        for trans in reg_types:
            url = '/api/promo/getsecavail'
            data = {
                'tr@ns': trans,  # make the args bad
                'imsi': self.imsi,
                'dest': destination,
                'balance': balance
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(response.data)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(status[i], 400)
            self.assertEqual(output[i], 'Missing Args')


class BulkAndUnliCommonPromoTest(BaseClass):

    @classmethod
    def setUpClass(cls):
        super(BulkAndUnliCommonPromoTest, cls).setUpClass()
        cls.imsi = 'IMSI001010000009999'

    @classmethod
    def tearDownClass(cls):
        super(BulkAndUnliCommonPromoTest, cls).tearDownClass()

    def test_get_required_minimum_balance(self):
        """For Bulk and Unli promo types, it should always return 1 peso"""
        reg_types = ['B_local_sms', 'B_local_call',
                     'B_outside_sms', 'B_outside_call',
                     'U_local_sms', 'U_local_call',
                     'U_outside_sms', 'U_outside_call',
                     ]
        tariff_data = []
        for i in reg_types:
            tariff_data.append(str(random.randint(0, 100)))
        codes, data = self.get_required_minimum_balance(reg_types, tariff_data)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], '1')

    def test_get_service_tariff(self):
        """"For Bulk and Unli promo types, it should always return 0"""
        reg_types = ['B_local_sms', 'B_local_call',
                     'B_outside_sms', 'B_outside_call',
                     'U_local_sms', 'U_local_call',
                     'U_outside_sms', 'U_outside_call',
                     ]
        destination = '123456789'
        codes, data = self.get_service_tariff(reg_types, destination)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 0)


class BulkPromoTest(BaseClass):

    @classmethod
    def setUpClass(cls):
        super(BulkPromoTest, cls).setUpClass()
        """We create a subscriber and a bulk promo"""

        # create test subscriber
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.quota = [random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100)]

        cls.promo_bulk = models.Promo(author=cls.admin,
                                      name='Bulk Promo',
                                      price=float_to_mc(10),
                                      promo_type='B',
                                      keyword='BULKPROMO',
                                      number='555',
                                      local_sms=cls.quota[0],
                                      local_call=cls.quota[1],
                                      outside_sms=cls.quota[2],
                                      outside_call=cls.quota[3])
        cls.promo_bulk.save()

        cls.promo_not_bulk = models.Promo(author=cls.admin,
                                          name='Not a Bulk Promo',
                                          price=float_to_mc(10),
                                          promo_type='U',
                                          keyword='NOBULKPROM',
                                          number='555',
                                          local_sms=cls.quota[0],
                                          local_call=cls.quota[1],
                                          outside_sms=cls.quota[2],
                                          outside_call=cls.quota[3])

        cls.promo_not_bulk.save()
        cls.subscription = None

    @classmethod
    def tearDownClass(cls):
        super(BulkPromoTest, cls).tearDownClass()
        cls.subscriber.delete()
        cls.promo_bulk.delete()

    def setUp(self):
        """Make the client subscribe to Bulk promo every time we run a test"""
        self.subscription = models.PromoSubscription(
            promo=self.promo_bulk,
            contact=self.subscriber,
            date_expiration=timezone.now() + timedelta(
                self.promo_bulk.validity),
            local_sms=self.promo_bulk.local_sms,
            local_call=self.promo_bulk.local_call,
            outside_sms=self.promo_bulk.outside_sms,
            outside_call=self.promo_bulk.outside_call)
        self.subscription.save()

    def tearDown(self):
        self.subscription.delete()

    def test_get_service_type(self):
        """ We should get the bulk promo service types since we
            are subscribed to a bulk promo
        """
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     ]
        dest = ['63999999123', '63999999123',
                '1999999123', '1999999123'
                ]
        expected = ['B_local_sms', 'B_local_call',
                    'B_outside_sms', 'B_outside_call',
                    ]
        codes, data = self.get_service_type(reg_types, dest)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_quota_deduct_random(self):
        """We should be able to deduct from Bulk promo quotas correctly"""
        reg_types = ['B_local_sms', 'B_local_call',
                     'B_outside_sms', 'B_outside_call',
                     ]
        amount = []
        expected = []
        for i in xrange(0, len(reg_types)):
            num = random.randint(0, 100)
            amount.append(num)
            if self.quota[i] - num > 0:
                expected.append(self.quota[i] - num)
            else:
                expected.append(self.quota[i])
        codes, data = self.quota_deduct(reg_types, amount)
        self.subscription.refresh_from_db()
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 'OK')
            key = 'self.subscription.' + reg_types[i][2:]
            current_quota = eval(key)
            self.assertEqual(current_quota, expected[i])

    def test_quota_deduct_bad_args(self):
        """Request fails if we pass bad arguments"""
        reg_types = ['B_local_sms', 'B_local_call',
                     'B_outside_sms', 'B_outside_call',
                     ]
        status = []
        output = []
        for i in xrange(0, len(reg_types)):
            url = '/api/promo/deduct'
            data = {
                'trAns': reg_types[i],  # make the args bad
                'iMsi': self.imsi,
                'amount': '1'
            }
            header = {}
            response = self.client.post(url, data=data, **header)
            status.append(response.status_code)
            output.append(response.data)
        self.subscription.refresh_from_db()
        for i in xrange(0, len(reg_types)):
            self.assertEqual(status[i], 400)
            self.assertEqual(output[i], 'Missing Args')

    def test_quota_deduct_from_a_non_bulk_promo(self):
        """ Deducting quotas should not apply if the promo
            is not a 'BULK' promo type
        """
        reg_types = ['U_local_sms', 'U_local_call',
                     'G_outside_sms', 'G_outside_call',
                     ]
        amount = []
        for i in xrange(0, len(reg_types)):
            num = random.randint(0, 100)
            amount.append(num)
        codes, data = self.quota_deduct(reg_types, amount)
        self.subscription.refresh_from_db()
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 400)
            self.assertEqual(data[i], 'Not Bulk promo')

    def test_get_sec_avail_call_quota_less_than_max_promo_call_duration(self):
        """ If a subscriber has bulk call quota of less than 3 mins,
            call duration depend on the available quota
        """
        max_duration = int(self.key1.value) / 60
        self.subscription.local_call = random.randint(1, max_duration)
        self.subscription.outside_call = random.randint(1, max_duration)
        self.subscription.save()
        expected = [self.subscription.local_call * 60,
                    self.subscription.outside_call * 60
                    ]
        reg_types = ['B_local_call', 'B_outside_call']
        destination = '12345678'
        balance = 10000000
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_sec_avail_call_quota_more_than_max_promo_call_duration(self):
        """ If a subscriber has bulk call quota of more than 3 mins,
            call duration must be capped to 3mins (180secs)
        """
        max_duration = int(self.key1.value) / 60
        self.subscription.local_call = random.randint(max_duration, 10)
        self.subscription.outside_call = random.randint(max_duration, 10)
        self.subscription.save()
        reg_types = ['B_local_call', 'B_outside_call']
        destination = '12345678'
        balance = 10000000
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 180)

    def test_quota_deduct_maxed_out(self):
        """We should be able to deduct from Bulk promo quotas correctly
        when we max out the allocation in one go"""
        reg_types = ['B_local_sms', 'B_local_call',
                     'B_outside_sms', 'B_outside_call',
                     ]
        codes, data = self.quota_deduct(reg_types, self.quota)
        self.subscription.refresh_from_db()
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 'OK')
            key = 'self.subscription.' + reg_types[i][2:]
            current_quota = eval(key)
            self.assertEqual(current_quota, 0)


class UnliPromoTest(BaseClass):

    @classmethod
    def setUpClass(cls):
        super(UnliPromoTest, cls).setUpClass()
        """We create a subscriber and a promo"""

        # create test subscriber
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.promo_unli = models.Promo(author=cls.admin,
                                      name='Unlimited Promo',
                                      price=float_to_mc(10),
                                      promo_type='U',
                                      keyword='UNLIPROMO',
                                      number='555',
                                      local_sms=1,
                                      local_call=1,
                                      outside_sms=1,
                                      outside_call=1)

        cls.promo_unli.save()
        cls.subscription = None

    @classmethod
    def tearDownClass(cls):
        super(UnliPromoTest, cls).tearDownClass()
        cls.subscriber.delete()
        cls.promo_unli.delete()

    def setUp(self):
        """Make the client subscribe to Bulk promo every time we run a test"""
        self.subscription = models.PromoSubscription(
            promo=self.promo_unli,
            contact=self.subscriber,
            date_expiration=timezone.now() + timedelta(
                self.promo_unli.validity),
            local_sms=self.promo_unli.local_sms,
            local_call=self.promo_unli.local_call,
            outside_sms=self.promo_unli.outside_sms,
            outside_call=self.promo_unli.outside_call)
        self.subscription.save()

    def tearDown(self):
        self.subscription.delete()

    def test_get_sec_avail(self):
        """For Unli promo types, it should always return 180."""
        reg_types = ['U_local_call', 'U_outside_call',
                     ]
        destination = '12345678'
        balance = 10000000
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 180)

    def test_get_service_type(self):
        """ We should get the bulk promo service types since we
            are subscribed to a bulk promo
        """
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     ]
        dest = ['63999999123', '63999999123',
                '1999999123', '1999999123'
                ]
        expected = ['U_local_sms', 'U_local_call',
                    'U_outside_sms', 'U_outside_call',
                    ]
        codes, data = self.get_service_type(reg_types, dest)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])


class DiscountedPromoTest(BaseClass):

    @classmethod
    def setUpClass(cls):
        super(DiscountedPromoTest, cls).setUpClass()
        """We create a subscriber and a promo"""

        # create test subscriber
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.promo_disc = models.Promo(
            author=cls.admin,
            name='Discounted Promo',
            price=float_to_mc(10),
            promo_type='D',
            keyword='DISCPROMO',
            number='555',
            local_sms=float_to_mc(random.randint(1, 10)),
            local_call=float_to_mc(random.randint(1, 10)),
            outside_sms=float_to_mc(random.randint(1, 10)),
            outside_call=float_to_mc(random.randint(1, 10))
        )

        cls.promo_disc.save()
        cls.subscription = None

    @classmethod
    def tearDownClass(cls):
        super(DiscountedPromoTest, cls).tearDownClass()
        cls.subscriber.delete()
        cls.promo_disc.delete()

    def setUp(self):
        """Make the client subscribe to Bulk promo every time we run a test"""
        self.subscription = models.PromoSubscription(
            promo=self.promo_disc,
            contact=self.subscriber,
            date_expiration=timezone.now() + timedelta(
                self.promo_disc.validity),
            local_sms=self.promo_disc.local_sms,
            local_call=self.promo_disc.local_call,
            outside_sms=self.promo_disc.outside_sms,
            outside_call=self.promo_disc.outside_call)
        self.subscription.save()

    def tearDown(self):
        self.subscription.delete()

    def test_get_service_type(self):
        """ We should get the discounted promo service types since we
            are subscribed to a bulk promo
        """
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     ]
        dest = ['63999999123', '63999999123',
                '1999999123', '1999999123'
                ]
        expected = ['D_local_sms', 'D_local_call',
                    'D_outside_sms', 'D_outside_call',
                    ]
        codes, data = self.get_service_type(reg_types, dest)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_required_minimum_balance(self):
        """ We should get whatever tariff rates are passed to
            get_required_min_balance
        """
        reg_types = ['D_local_sms', 'D_local_call',
                     'D_outside_sms', 'D_outside_call',
                     ]
        tariff_data = []
        for i in reg_types:
            tariff_data.append(str(random.randint(0, 100)))
        codes, data = self.get_required_minimum_balance(reg_types, tariff_data)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], tariff_data[i])

    def test_get_service_tariff(self):
        """ We should get the discounted tariff rates as dictated by the
            promo availed by the subscriber
        """
        reg_types = ['D_local_sms', 'D_local_call',
                     'D_outside_sms', 'D_outside_call',
                     ]
        expected = []
        destination = '123456789'
        for i in reg_types:
            key = 'self.subscription.' + i[2:]
            expected.append(eval(key))  # convert to mc
        codes, data = self.get_service_tariff(reg_types, destination)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_sec_avail_with_big_account_balance(self):
        """ For discounted promo types, it depends on the available balance.
            For this case, it will max up to 180 secs since we have a
            'big' account balance
        """
        reg_types = ['D_local_call', 'D_outside_call',
                     ]
        destination = '12345678'
        balance = 10000000
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 180)

    def test_get_sec_avail_with_small_account_balance(self):
        """ For discounted promo types, it depends on the available balance.
            For this case, it should be less than 180
        """
        reg_types = ['D_local_call', 'D_outside_call',
                     ]
        expected = []
        destination = '12345678'
        balance = 10
        for i in reg_types:
            key = 'self.subscription.' + i[2:]
            expected.append(balance / (eval(key)))
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_sec_avail_with_no_balance(self):
        """ For discounted promo types, it depends on the available balance.
            For this case, since no balance, should return 0
        """
        reg_types = ['D_local_call', 'D_outside_call',
                     ]
        destination = '12345678'
        balance = 0
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 0)


class PromoSubscriptionTest(BaseClass):

    @classmethod
    def setUpClass(cls):
        super(PromoSubscriptionTest, cls).setUpClass()
        """We create a subscriber and a bulk promo"""

        # create test subscriber
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.quota = [random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100)]

        cls.promo = models.Promo(author=cls.admin,
                                 name='Any Any Promo',
                                 price=float_to_mc(10),
                                 promo_type=random.choice(
                                     ['B', 'D', 'U', 'G']),
                                 keyword='ANYPROMO',
                                 number='555',
                                 local_sms=cls.quota[0],
                                 local_call=cls.quota[1],
                                 outside_sms=cls.quota[2],
                                 outside_call=cls.quota[3])
        cls.promo.save()

    @classmethod
    def tearDownClass(cls):
        super(PromoSubscriptionTest, cls).tearDownClass()
        cls.subscriber.delete()
        cls.promo.delete()

    def test_subscribe_normal(self):
        """We can subscribe to a promo"""
        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo.keyword,
                                             10000000)
        self.assertEqual(code, 200)
        self.assertEqual(data, 'OK SUBSCRIBE')

    def test_subscribe_zero_balance(self):
        """We cannot subscribe to a promo, since we have no remaining balance"""
        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo.keyword, 0)
        self.assertEqual(code, 402)
        self.assertEqual(data, 'Insufficient balance')

    def test_subscribe_insufficient_balance(self):
        """ We cannot subscribe to a promo, since we have a non-zero balance
            but it is not enough
        """
        balance = float_to_mc(2.50)
        # check that balance is really less than promo price
        self.assertTrue(balance < self.promo.price)
        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo.keyword,
                                             balance)
        self.assertEqual(code, 402)
        self.assertEqual(data, 'Insufficient balance')

    def test_unsubscribe_normal(self):
        """We can opt out of a promo subscription"""
        self.subscribe_to_promo(self.imsi, self.promo.keyword, 100000000)
        code, data = self.unsubscribe_to_promo(self.imsi,
                                               self.promo.keyword)
        self.assertEqual(code, 200)
        self.assertEqual(data, 'OK UNSUBSCRIBE')

    def test_subscribe_invalid_keyword(self):
        """We cannot subscribe because we entered an invalid promo keyword."""
        code, data = self.subscribe_to_promo(self.imsi,
                                             'invalid Keyword',
                                             10000000)
        self.assertEqual(code, 400)
        self.assertEqual(data, 'Bad promo request')

    def test_unsubscribe_invalid(self):
        """We cannot opt out because we entered an invalid promo keyword."""
        code, data = self.unsubscribe_to_promo(self.imsi,
                                               'invalid Keyword')
        self.assertEqual(code, 200)
        self.assertEqual(data, 'FAIL UNSUBSCRIBE')

    def test_subscribe_twice(self):
        """We can subscribe multiple times to a promo"""
        for i in xrange(0, random.randint(0, 10)):
            code, data = self.subscribe_to_promo(self.imsi,
                                                 self.promo.keyword,
                                                 100000000)
            self.assertEqual(code, 200)
            self.assertEqual(data, 'OK SUBSCRIBE')

    def test_subscribe_bad_args(self):
        """We cannot subscribe to a promo the request has bad arguments """
        endaga_sub.get_account_balance = Mock(return_value=10000000)
        endaga_sub.subtract_credit = Mock(return_value=None)
        send_sms.delay = Mock(return_value=None)
        purge_entry.apply_async = Mock(return_value=None)

        url = '/api/promo/subscribe'
        data = {
            'imsI': self.imsi,  # make the args bad
            'keyW0rd': self.promo.keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Missing Args')

    def test_unsubscribe_bad_args(self):
        """We cannot unsubscribe to a promo the request has bad arguments """
        self.subscribe_to_promo(self.imsi, self.promo.keyword, 100000000)

        endaga_sub.get_account_balance = Mock(return_value=10000000)
        endaga_sub.subtract_credit = Mock(return_value=None)
        send_sms.delay = Mock(return_value=None)
        purge_entry.apply_async = Mock(return_value=None)

        url = '/api/promo/unsubscribe'
        data = {
            'imsI': self.imsi,  # make the args bad
            'keyW0rd': self.promo.keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Missing Args')

        # Do a normal unsubscribe, just to clean up
        code, data = self.unsubscribe_to_promo(self.imsi,
                                               self.promo.keyword)
        self.assertEqual(code, 200)
        self.assertEqual(data, 'OK UNSUBSCRIBE')

    def test_subscribe_normal_imsi_not_in_vbts_table(self):
        """
            We cannot subscribe to a promo if we are not
            registered to the VBTS databse.
        """
        endaga_sub.get_numbers_from_imsi = Mock(return_value='639999')
        code, data = self.subscribe_to_promo('IMSI001111119988',
                                             self.promo.keyword,
                                             10000000)
        self.assertEqual(code, 404)
        self.assertEqual(data, 'Not Found')


class PromoLimitsTest(BaseClass):

    """ We are testing our optional promo config keys here. """

    @classmethod
    def setUpClass(cls):
        super(PromoLimitsTest, cls).setUpClass()

        # create test subscriber
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.quota = [random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100)]

        cls.promo1 = models.Promo(author=cls.admin,
                                  name='Promo1',
                                  price=float_to_mc(10),
                                  promo_type=random.choice(
                                      ['B', 'D', 'U', 'G']),
                                  keyword='PROMO1',
                                  number='555',
                                  local_sms=cls.quota[0],
                                  local_call=cls.quota[1],
                                  outside_sms=cls.quota[2],
                                  outside_call=cls.quota[3])
        cls.promo1.save()

        cls.promo2 = models.Promo(author=cls.admin,
                                  name='Promo2',
                                  price=float_to_mc(10),
                                  promo_type=random.choice(
                                      ['B', 'D', 'U', 'G']),
                                  keyword='PROMO2',
                                  number='555',
                                  local_sms=cls.quota[0],
                                  local_call=cls.quota[1],
                                  outside_sms=cls.quota[2],
                                  outside_call=cls.quota[3])
        cls.promo2.save()

    @classmethod
    def tearDownClass(cls):
        super(PromoLimitsTest, cls).tearDownClass()
        cls.subscriber.delete()
        cls.promo1.delete()
        cls.promo2.delete()

    def test_unlimited_promo_subscriptions(self):
        """We can subscribe to any promo, any number of times"""

        # we start with zero subscriptions
        self.assertEqual(0, models.PromoSubscription.objects.all().count())

        # subscribe X times to promo1
        # use defined limit, show later that we can exceed it
        i = 0
        while i < int(self.key3.value):
            code, data = self.subscribe_to_promo(self.imsi,
                                                 self.promo1.keyword,
                                                 10000000)
            self.assertEqual(code, 200)
            self.assertEqual(data, 'OK SUBSCRIBE')
            # subscription count gets incremented
            i += 1
            self.assertEqual(i, models.PromoSubscription.objects.all().count())

        # let's try to subscribe to promo2, we should be able to do so
        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo2.keyword,
                                             10000000)
        self.assertEqual(code, 200)
        self.assertEqual(data, 'OK SUBSCRIBE')
        # subscription count should increment
        self.assertEqual(i + 1, models.PromoSubscription.objects.all().count())

        # try again to Promo1, we should be able to do so
        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo1.keyword,
                                             10000000)
        self.assertEqual(code, 200)
        self.assertEqual(data, 'OK SUBSCRIBE')
        # subscription count should increment
        self.assertEqual(i + 2, models.PromoSubscription.objects.all().count())

    def test_limit_number_of_subscriptions_per_promo(self):
        """ We limit the number of times the subscriber can subscribe per promo.
            We should not be allowed to exceed this limit.
            For example: limit is 1 per promo. therefore, we can subscribe once
            to Promo1 and another one to Promo2
        """
        # update our keys to appropriate values
        # promo_limit_type = 'A' (Limit number of subscription per promo)

        self.key2.value = 'A'  # promo_limit_type
        self.key2.save()
        self.key3.value = random.randint(1, 10)  # max_promo_subscription
        self.key3.save()

        # we start with zero subscriptions
        self.assertEqual(0, models.PromoSubscription.objects.all().count())

        # subscribe X times to promo1, use defined limit
        i = 0
        while i < int(self.key3.value):
            code, data = self.subscribe_to_promo(self.imsi,
                                                 self.promo1.keyword,
                                                 10000000)
            self.assertEqual(code, 200)
            self.assertEqual(data, 'OK SUBSCRIBE')
            # subscription count gets incremented
            i += 1
            self.assertEqual(i, models.PromoSubscription.objects.all().count())

        # let's try to subscribe to promo1, this should exceed limit
        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo1.keyword,
                                             10000000)
        self.assertEqual(code, 403)
        self.assertEqual(data, 'Too Many Subscriptions')
        # subscription count should be the same
        self.assertEqual(i, models.PromoSubscription.objects.all().count())

        # subscribe X times to promo2, use defined limit
        j = 0
        while j < int(self.key3.value):
            code, data = self.subscribe_to_promo(self.imsi,
                                                 self.promo2.keyword,
                                                 10000000)
            self.assertEqual(code, 200)
            self.assertEqual(data, 'OK SUBSCRIBE')
            # subscription count gets incremented
            j += 1
            self.assertEqual(j + i,  # factor in subscriptions for Promo1
                             models.PromoSubscription.objects.all().count())

        # let's try to subscribe to promo2, this should exceed limit
        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo2.keyword,
                                             10000000)
        self.assertEqual(code, 403)
        self.assertEqual(data, 'Too Many Subscriptions')
        # subscription count should be the same
        self.assertEqual(j + i, models.PromoSubscription.objects.all().count())

    def test_limit_number_of_subscriptions_for_all_promos(self):
        """ We limit the number of times the subscriber can subscribe
            for all promos. We should not be allowed to exceed this limit.
            For example: limit is 1 for all promo. therefore,
            we can subscribe once
        """
        # update our keys to appropriate values
        # promo_limit_type = 'B' (Limit number of subscription for all promos)

        self.key2.value = 'B'  # promo_limit_type
        self.key2.save()
        self.key3.value = random.randint(1, 10)  # max_promo_subscription
        self.key3.save()

        # we start with zero subscriptions
        self.assertEqual(0, models.PromoSubscription.objects.all().count())

        # subscribe X times either promo1 or promo2
        # use defined limit, show later that we can exceed it
        i = 0
        while i < int(self.key3.value):
            _promo = random.choice([self.promo1.keyword, self.promo2.keyword])
            code, data = self.subscribe_to_promo(self.imsi, _promo, 10000000)
            self.assertEqual(code, 200)
            self.assertEqual(data, 'OK SUBSCRIBE')
            # subscription count gets incremented
            i += 1
            self.assertEqual(i, models.PromoSubscription.objects.all().count())

        # let's try to subscribe to a promo, we should be able to do so
        _promo = random.choice([self.promo1.keyword, self.promo2.keyword])
        code, data = self.subscribe_to_promo(self.imsi, _promo, 10000000)
        self.assertEqual(code, 403)
        self.assertEqual(data, 'Too Many Subscriptions')
        # subscription count should be the same
        self.assertEqual(i, models.PromoSubscription.objects.all().count())


class PromoStatusTest(BaseClass):
    @classmethod
    def setUpClass(cls):
        super(PromoStatusTest, cls).setUpClass()
        """We create a subscriber and a bulk promo"""

        # create test subscriber
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.quota = [random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100)]

        cls.promo = models.Promo(author=cls.admin,
                                 name='Any Any Promo',
                                 price=float_to_mc(10),
                                 promo_type=random.choice(
                                     ['B', 'D', 'U', 'G']),
                                 keyword='ANYPROMO',
                                 number='555',
                                 local_sms=cls.quota[0],
                                 local_call=cls.quota[1],
                                 outside_sms=cls.quota[2],
                                 outside_call=cls.quota[3])
        cls.promo.save()

    @classmethod
    def tearDownClass(cls):
        super(PromoStatusTest, cls).tearDownClass()
        cls.subscriber.delete()
        cls.promo.delete()

    def test_get_status_normal(self):
        """We can get our promo status"""
        endaga_sub.get_numbers_from_imsi = Mock(return_value='639999000000')
        send_sms.delay = Mock(return_value=None)
        self.subscribe_to_promo(self.imsi, self.promo.keyword, 1000000)

        url = '/api/promo/status'
        data = {
            'imsi': self.imsi,
            'keyword': self.promo.keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'OK')

    def test_get_status_normal_no_subscription(self):
        """ We can get our promo status even if we are
            not subscribed to a promo
        """
        endaga_sub.get_numbers_from_imsi = Mock(return_value='639999000000')
        send_sms.delay = Mock(return_value=None)

        url = '/api/promo/status'
        data = {
            'imsi': self.imsi,
            'keyword': self.promo.keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'OK')

    def test_get_status_normal_bad_args(self):
        endaga_sub.get_numbers_from_imsi = Mock(return_value='639999000000')
        send_sms.delay = Mock(return_value=None)

        url = '/api/promo/status'
        data = {
            'iMsi': self.imsi,  # make the args bad
            'keyword': self.promo.keyword
        }
        header = {}
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Missing Args')


class MayPromoPeroUbosNaAngQuota(BaseClass):
    @classmethod
    def setUpClass(cls):
        super(MayPromoPeroUbosNaAngQuota, cls).setUpClass()
        """We create a subscriber and a promo"""

        # create test subscriber
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.promo_disc = models.Promo(
            author=cls.admin,
            name='Discounted Promo',
            price=float_to_mc(10),
            promo_type='D',
            keyword='DISCPROMO',
            number='555',
            local_sms=float_to_mc(random.randint(1, 10)),
            local_call=float_to_mc(random.randint(1, 10)),
            outside_sms=float_to_mc(random.randint(1, 10)),
            outside_call=float_to_mc(random.randint(1, 10))
        )

        cls.promo_disc.save()
        cls.subscription = None

    @classmethod
    def tearDownClass(cls):
        super(MayPromoPeroUbosNaAngQuota, cls).tearDownClass()
        cls.subscriber.delete()
        cls.promo_disc.delete()

    def setUp(self):
        """Make the client subscribe to Bulk promo every time we run a test"""
        self.subscription = models.PromoSubscription(
            promo=self.promo_disc,
            contact=self.subscriber,
            date_expiration=timezone.now() + timedelta(
                self.promo_disc.validity),
            local_sms=0,        # zero na ang quota
            local_call=0,
            outside_sms=0,
            outside_call=0)
        self.subscription.save()

    def tearDown(self):
        self.subscription.delete()

    def test_get_service_type(self):
        """ We should get the regular service types since our
            promo quotas are zero
        """
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     ]
        dest = ['63999999123', '63999999123',
                '1999999123', '1999999123'
                ]
        # expected = ['D_local_sms', 'D_local_call',
        #             'D_outside_sms', 'D_outside_call',
        #             ]
        expected = reg_types
        codes, data = self.get_service_type(reg_types, dest)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])


class PromoRequiredMinBalanceTest(BaseClass):
    @classmethod
    def setUpClass(cls):
        super(PromoRequiredMinBalanceTest, cls).setUpClass()

        # create test subscriber
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)
        cls.subscriber.save()

        cls.quota = [random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100),
                     random.randint(1, 100)]

        cls.promo1 = models.Promo(author=cls.admin,
                                  name='Promo1',
                                  price=float_to_mc(10),
                                  promo_type=random.choice(
                                      ['B', 'D', 'U', 'G']),
                                  keyword='PROMO1',
                                  number='555',
                                  local_sms=cls.quota[0],
                                  local_call=cls.quota[1],
                                  outside_sms=cls.quota[2],
                                  outside_call=cls.quota[3])
        cls.promo1.save()

    @classmethod
    def tearDownClass(cls):
        super(PromoRequiredMinBalanceTest, cls).tearDownClass()
        cls.subscriber.delete()
        cls.promo1.delete()

    def test_normal_satisfies_req_min_bal(self):
        """ Our subscriber has enough credit and thus satisfies
            the required minimum balance requirement
        """

        # we start with zero subscriptions
        self.assertEqual(0, models.PromoSubscription.objects.all().count())

        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo1.keyword,
                                             balance=float_to_mc(100))

        self.assertEqual(code, 200)
        self.assertEqual(data, 'OK SUBSCRIBE')
        self.assertEqual(1, models.PromoSubscription.objects.all().count())

    def test_failed_req_min_bal(self):
        """ Our subscriber does not have enough credit and
            should not be able to subscribe to promo
        """
        # we start with zero subscriptions
        self.assertEqual(0, models.PromoSubscription.objects.all().count())

        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo1.keyword,
                                             balance=float_to_mc(1))

        self.assertEqual(code, 402)
        self.assertEqual(data, 'Insufficient balance')
        self.assertEqual(0, models.PromoSubscription.objects.all().count())

    def test_normal_config_is_decimal(self):
        """ Config should still work even if the admin inputted a decimal
        """

        self.key4.value = '2.50'  # promo_limit_type
        self.key4.save()

        # we start with zero subscriptions
        self.assertEqual(0, models.PromoSubscription.objects.all().count())

        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo1.keyword,
                                             balance=float_to_mc(100))

        self.assertEqual(code, 200)
        self.assertEqual(data, 'OK SUBSCRIBE')
        self.assertEqual(1, models.PromoSubscription.objects.all().count())

    def test_failed_config_is_decimal(self):
        """ Our subscriber does not have enough credit and
            should not be able to subscribe to promo.
            Config should still work even if the admin inputted a decimal
        """
        # we start with zero subscriptions
        self.assertEqual(0, models.PromoSubscription.objects.all().count())

        code, data = self.subscribe_to_promo(self.imsi,
                                             self.promo1.keyword,
                                             balance=float_to_mc(1.50))

        self.assertEqual(code, 402)
        self.assertEqual(data, 'Insufficient balance')
        self.assertEqual(0, models.PromoSubscription.objects.all().count())
