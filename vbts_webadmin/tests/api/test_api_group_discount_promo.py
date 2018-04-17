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
from vbts_webadmin.tests.api.test_api_promo import BaseClass


class GroupDiscountPromoTest(BaseClass):

    @classmethod
    def setUpClass(cls):
        super(GroupDiscountPromoTest, cls).setUpClass()
        cls.imsi = 'IMSI001010000009999'
        cls.callerid = '639991111111'
        cls.subscriber = models.Contact(imsi=cls.imsi,
                                        callerid=cls.callerid)

        cls.subscriber.save()

        cls.quota = [float_to_mc(random.randint(1, 10)),
                     float_to_mc(random.randint(1, 10)),
                     float_to_mc(random.randint(1, 10)),
                     float_to_mc(random.randint(1, 10))]

        cls.promo = models.Promo(author=cls.admin,
                                 name='Group Discount Promo',
                                 price=float_to_mc(10),
                                 promo_type='G',
                                 keyword='GPROMO',
                                 number='555',
                                 local_sms=cls.quota[0],
                                 local_call=cls.quota[1],
                                 outside_sms=cls.quota[2],
                                 outside_call=cls.quota[3])
        cls.promo.save()
        cls.subscription = None

        # Create a dummy group and group members
        # From FS, we are passing in group name in uppercase

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
        super(GroupDiscountPromoTest, cls).tearDownClass()
        cls.subscriber.delete()
        cls.promo.delete()
        cls.subscriber1.delete()
        cls.subscriber2.delete()
        cls.dummygroup.delete()
        cls.gm1.delete()

    def setUp(self):
        """ Make the client subscribe to a discounted promo
            every time we run a test
        """
        self.subscription = models.PromoSubscription(
            promo=self.promo,
            contact=self.subscriber,
            date_expiration=timezone.now() + timedelta(
                self.promo.validity),
            local_sms=self.promo.local_sms,
            local_call=self.promo.local_call,
            outside_sms=self.promo.outside_sms,
            outside_call=self.promo.outside_call)
        self.subscription.save()

    def tearDown(self):
        """ Delete the subscription after every test """
        self.subscription.delete()

    def test_get_service_type_normal(self):
        """ We should get the group discount service types since we
            are subscribed to a group discount promo and our destination
            numbers are defined in our group
        """
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     ]
        dest = [self.subscriber1.callerid, self.subscriber1.callerid,
                self.subscriber1.callerid, self.subscriber1.callerid
                ]
        expected = ['G_local_sms', 'G_local_call',
                    'G_outside_sms', 'G_outside_call',
                    ]
        codes, data = self.get_service_type(reg_types, dest)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_service_type_dest_not_in_group(self):
        """ We should get the regular service types because although we
            are subscribed to a group discount promo, our destination
            numbers are NOT defined in our group
        """
        reg_types = ['local_sms', 'local_call',
                     'outside_sms', 'outside_call',
                     ]
        dest = [self.subscriber2.callerid, self.subscriber2.callerid,
                self.subscriber2.callerid, self.subscriber2.callerid
                ]
        expected = ['local_sms', 'local_call',
                    'outside_sms', 'outside_call',
                    ]
        codes, data = self.get_service_type(reg_types, dest)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_required_minimum_balance(self):
        """ We should get whatever tariff rates are passed to
            get_required_min_balance
        """
        reg_types = ['G_local_sms', 'G_local_call',
                     'G_outside_sms', 'G_outside_call',
                     ]
        tariff_data = []
        for i in reg_types:
            tariff_data.append(str(random.randint(0, 100)))
        codes, data = self.get_required_minimum_balance(reg_types,
                                                        tariff_data)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], tariff_data[i])

    def test_get_service_tariff(self):
        """ We should get the group discount tariff rates as dictated by the
            promo availed by the subscriber
        """
        reg_types = ['G_local_sms', 'G_local_call',
                     'G_outside_sms', 'G_outside_call',
                     ]
        expected = []
        destination = self.subscriber1.callerid
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
        reg_types = ['G_local_call', 'G_outside_call',
                     ]
        destination = self.subscriber1.callerid
        balance = 10000000
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 180)

    def test_get_sec_avail_with_small_account_balance(self):
        """ For group discount promo types, it depends on the available balance.
            For this case, it should be less than 180
        """
        reg_types = ['G_local_call', 'G_outside_call',
                     ]
        expected = []
        destination = self.subscriber1.callerid
        balance = 10
        for i in reg_types:
            key = 'self.subscription.' + i[2:]
            expected.append(balance / (eval(key)))
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], expected[i])

    def test_get_sec_avail_with_no_balance(self):
        """ For group discount promo types, it depends on the available balance.
            For this case, since no balance, should return 0
        """
        reg_types = ['G_local_call', 'G_outside_call',
                     ]
        destination = self.subscriber1.callerid
        balance = 0
        codes, data = self.get_sec_avail(reg_types, destination, balance)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], 0)

    def test_get_correct_tariff_for_dest(self):
        """ If destination is a member of the sender's group, and the sender has
            a group discount promo, then DISCOUNTED rates should be applied.
        """
        reg_types = ['G_local_sms', 'G_local_call',
                     'G_outside_sms', 'G_outside_call',
                     ]
        destination = self.subscriber1.callerid
        codes, data = self.get_service_tariff(reg_types, destination)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertEqual(data[i], self.quota[i])

    def test_get_correct_tariff_for_dest_not_in_group(self):
        """ If destination is NOT a member of the sender's group, and the sender has
            a group discount promo, then REGULAR rates should be applied.
        """
        reg_types = ['G_local_sms', 'G_local_call',
                     'G_outside_sms', 'G_outside_call',
                     ]
        destination = self.subscriber2.callerid
        codes, data = self.get_service_tariff(reg_types, destination)
        for i in xrange(0, len(reg_types)):
            self.assertEqual(codes[i], 200)
            self.assertNotEqual(data[i], self.quota[i])
