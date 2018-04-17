"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db import transaction
from django.test import Client
from django.test import TestCase

from vbts_webadmin import models
from vbts_webadmin.utils import float_to_mc


class PromoViewTest(TestCase):

    """Testing Promo UI views"""

    @classmethod
    def setUpClass(cls):
        cls.username = 'Y'
        cls.password = 'YY'
        cls.user = User(username=cls.username, email='X@X.com')
        cls.user.set_password(cls.password)
        cls.user.save()

        cls.test_promo = models.Promo(author=cls.user,
                                      name='Bulk Promo',
                                      price=float_to_mc(10),
                                      promo_type='B',
                                      keyword='BULKPROMO',
                                      validity='2',
                                      local_sms=10,
                                      local_call=10,
                                      outside_sms=10,
                                      outside_call=10)
        cls.test_promo.save()

        # Create a subscriber and make him subscribe to our dummy promo
        cls.manuel = models.Contact(imsi='IMSI00101000000000',
                                    callerid='63999000000')
        cls.manuel.save()
        cls.subscription = models.PromoSubscription(promo=cls.test_promo,
                                                    contact=cls.manuel,
                                                    local_sms=10,
                                                    local_call=10,
                                                    outside_sms=10,
                                                    outside_call=10)
        cls.subscription.save()
        # Create a test client.
        cls.client = Client()

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.test_promo.delete()
        cls.manuel.delete()
        cls.subscription.delete()

    def login(self):
        """ Logs the client in """
        self.client.login(username=self.username, password=self.password)

    def logout(self):
        """ Logs the client out """
        self.client.logout()

    def tearDown(self):
        """ Make sure we log out the client after every test """
        self.logout()

    def test_promo_view_list_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        response = self.client.get('/dashboard/promos/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/dashboard/promos/', follow=True)
        self.assertRedirects(response, '/?next=/dashboard/promos/')

    def test_promo_view_list(self):
        """List down all the promos"""
        self.login()
        response = self.client.get('/dashboard/promos/')
        self.assertEqual(200, response.status_code)

    def test_promo_search_random(self):
        """Search a random keyword"""
        self.login()
        keyword = 'random'
        response = self.client.get('/dashboard/promos/?search=%s' % keyword)
        self.assertEqual(200, response.status_code)

    def test_promo_search_random_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        keyword = 'random'
        url = '/dashboard/promos/'
        data = {
            'search': keyword
        }
        response = self.client.get(url, data)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, data, follow=True)
        self.assertRedirects(response, '/?next=' + url + '%3Fsearch%3Drandom')

    def test_promo_view_delete(self):
        self.login()
        url = '/dashboard/promos/delete/%s' % self.test_promo.pk
        response = self.client.post(url)
        self.assertEqual(200, response.status_code)

    def test_promo_view_delete_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/promos/delete/%s' % self.test_promo.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_promo_view_update(self):
        self.login()
        url = '/dashboard/promos/update/%s' % self.test_promo.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_promo_view_update_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/promos/update/%s' % self.test_promo.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_promo_view_detail(self):
        self.login()
        url = '/dashboard/promos/detail/%s' % self.test_promo.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_promo_view_detail_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/promos/detail/%s' % self.test_promo.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_promo_view_broadcast_sms_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/promos/sms'
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_view_promo_subscription(self):
        self.login()
        """List down all the promo subscription"""
        response = self.client.get('/dashboard/promo/view_subscriptions')
        self.assertEqual(200, response.status_code)

    def test_promo_view_promo_subscription_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/promo/view_subscriptions'
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_delete_existing_promo(self):
        """We can delete a promo by POSTing to /dashboard/promo/delete."""
        self.login()
        # We should start with 1 promo
        self.assertEqual(1, models.Promo.objects.all().count())
        self.client.post('/dashboard/promo/delete/%s' % self.test_promo.pk)
        # And end up with none
        self.assertEqual(0, models.Promo.objects.all().count())

    def test_delete_non_existing_promo(self):
        """404 for attempting to access non-existent entries"""
        self.login()
        response = self.client.post('/dashboard/promo/delete/1000')
        self.assertEqual(404, response.status_code)

    def test_create_new_promo(self):
        """We should be able to create promo."""
        self.login()
        # We should start with 1 promo
        self.assertEqual(1, models.Promo.objects.all().count())
        data = {
            'name': 'sample promo',
            'description': 'This is a sample promo for our unit test.',
            'tmp_price': 10,
            'promo_type': 'U',
            'keyword': 'SAMPLE',
            'number': '111',
            'validity': 1,
            'unli_local_sms': True
        }
        self.client.post('/dashboard/promo/new', data)
        # Check promo entries in DB increased by 1
        self.assertEqual(2, models.Promo.objects.all().count())

    def test_create_new_promo_duplicate_name(self):
        """We should NOT be able to create promos with duplicate names."""
        self.login()
        # We should start with 1 promo
        self.assertEqual(1, models.Promo.objects.all().count())
        data = {
            'name': self.test_promo.name,  # same name as init data above
            'description': 'This is a sample promo for our unit test.',
            'tmp_price': 10,
            'promo_type': 'U',
            'keyword': 'SAMPLE',
            'number': '111',
            'validity': 1,
            'unli_local_sms': True
        }
        try:
            # Duplicates should be prevented.
            with transaction.atomic():
                self.client.post('/dashboard/promo/new', data)
        except IntegrityError:
            pass
        # number of promo objects should not increase
        self.assertEqual(1, models.Promo.objects.all().count())

    def test_create_new_promo_duplicate_keyword(self):
        """We should NOT be able to create promos with duplicate keyword."""
        self.login()
        # We should start with 1 promo
        self.assertEqual(1, models.Promo.objects.all().count())
        data = {
            'name': 'Banana',  # same name as init data above
            'description': 'This is a sample promo for our unit test.',
            'tmp_price': 10,
            'promo_type': 'U',
            'keyword': self.test_promo.keyword,
            'number': '111',
            'validity': 1,
            'unli_local_sms': True
        }
        try:
            # Duplicates should be prevented.
            with transaction.atomic():
                self.client.post('/dashboard/promo/new', data)
        except IntegrityError:
            pass
        # number of promo objects should not increase
        self.assertEqual(1, models.Promo.objects.all().count())

    def test_update_existing_promo(self):
        """We should be able to edit existing promo."""
        self.login()
        # We should start with 1 promo
        self.assertEqual(1, models.Promo.objects.all().count())
        data = {
            'name': 'updated promo name',
            'description': 'We are updating.',
            'tmp_price': 10,
            'promo_type': 'U',
            'keyword': 'SAMPLE',
            'number': '111',
            'validity': 1,
            'unli_local_sms': True
        }
        self.client.post('/dashboard/promo/update/%s'
                         % self.test_promo.pk, data)
        # Check data in DB to see if params have changed
        promo = models.Promo.objects.get(pk=self.test_promo.pk)
        self.assertEqual(data['name'], promo.name)
        self.assertEqual(data['description'], promo.description)

    def test_delete_existing_promo_subscription(self):
        """We can delete an existing promo subscription."""
        self.login()
        # We should start with 1 subscription to test_promo
        self.assertEqual(1, models.PromoSubscription.objects.
                         filter(promo=self.test_promo).count())
        self.client.post('/dashboard/promo/delete_subscription/%s'
                         % self.subscription.pk)
        # And end up with none
        self.assertEqual(0, models.PromoSubscription.objects.
                         filter(promo=self.test_promo).count())

    def test_delete_non_existing_promo_subscription(self):
        """404 for attempting to access non-existent entries"""
        self.login()
        response = self.client.post(
            '/dashboard/promo/delete_subscription/1000')
        self.assertEqual(404, response.status_code)
