"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase
from django.utils import timezone
from mock import Mock

from vbts_webadmin import models
from vbts_webadmin.tasks import send_sms


class CircleBaseTestClass(TestCase):
    """Base class for testing Circles UI views"""

    @classmethod
    def setUpClass(cls):
        """ Let's setup our testing workspace"""
        cls.username = 'X'
        cls.password = 'XX'
        cls.admin = User(username=cls.username, email='X@X.com')
        cls.admin.set_password(cls.password)
        cls.admin.save()

        # Fetch auto-created Contact for admin
        cls.admincontact = models.Contact.objects.get(
            imsi=settings.PCARI['ADMIN_IMSI'])

        # Create a test client.
        cls.client = Client()

    @classmethod
    def tearDownClass(cls):
        """ Clean them up! """
        cls.admin.delete()
        cls.admincontact.delete()

    def login(self):
        """ Logs the client in """
        self.client.login(username=self.username, password=self.password)

    def logout(self):
        """ Logs the client out """
        self.client.logout()

    def tearDown(self):
        """ Make sure we log out the client after every test """
        self.logout()


class CircleViewTest(CircleBaseTestClass):
    """Tests for Circles UI views"""

    @classmethod
    def setUpClass(cls):
        super(CircleViewTest, cls).setUpClass()
        # Create dummy circle
        cls.bilog = models.Circle(name='Circulo',
                                  description='Dummy text',
                                  owner=cls.admin)
        cls.bilog.save()

    @classmethod
    def tearDownClass(cls):
        super(CircleViewTest, cls).tearDownClass()
        cls.bilog.delete()

    def test_circle_view_list_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        response = self.client.get('/dashboard/circles/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/dashboard/circles/', follow=True)
        self.assertRedirects(response, '/?next=/dashboard/circles/')

    def test_circle_view_list(self):
        """List down all the circles"""
        self.login()
        response = self.client.get('/dashboard/circles/')
        self.assertEqual(200, response.status_code)

    def test_circle_search_random(self):
        """Search a random keyword"""
        self.login()
        keyword = 'random'
        response = self.client.get('/dashboard/circles/?search=%s' % keyword)
        self.assertEqual(200, response.status_code)

    def test_circle_search_random_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        keyword = 'random'
        url = '/dashboard/circles/'
        data = {
            'search': keyword
        }
        response = self.client.get(url, data)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, data, follow=True)
        self.assertRedirects(response, '/?next=' + url + '%3Fsearch%3Drandom')

    def test_circle_view_delete(self):
        self.login()
        url = '/dashboard/circle/delete/%s' % self.bilog.pk
        response = self.client.post(url)
        self.assertEqual(200, response.status_code)

    def test_circle_view_delete_get(self):
        self.login()
        url = '/dashboard/circle/delete/%s' % self.bilog.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_circle_view_delete_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/circle/delete/%s' % self.bilog.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_circle_view_update(self):
        self.login()
        url = '/dashboard/circle/update/%s' % self.bilog.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_circle_view_update_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/circle/update/%s' % self.bilog.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_circle_view_detail(self):
        self.login()
        url = '/dashboard/circle/view/%s' % self.bilog.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_circle_view_detail_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/circle/view/%s' % self.bilog.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_circle_view_broadcast_sms(self):
        self.login()
        url = '/dashboard/circle/broadcast'
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_circle_view_broadcast_sms_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/circle/broadcast'
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)


class CircleEmptyList(CircleBaseTestClass):
    """Testing pagination for empty group list"""

    def test_circle_view_list_empty(self):
        """Go to the empty list"""
        self.login()
        response = self.client.get('/dashboard/circles/')
        self.assertEqual(200, response.status_code)


class CircleLong(CircleBaseTestClass):
    """Testing pagination for *long* circle list"""

    @classmethod
    def setUpClass(cls):
        super(CircleLong, cls).setUpClass()
        for i in xrange(0, 20):
            models.Circle.objects.create(name='Circulo%d' % i,
                                         description='Dummy text',
                                         owner=cls.admin)

    @classmethod
    def tearDownClass(cls):
        super(CircleLong, cls).tearDownClass()
        models.Circle.objects.all().delete()

    def test_circle_view_list_long(self):
        """List down all the circles"""
        self.login()
        response = self.client.get('/dashboard/circles/')
        self.assertEqual(200, response.status_code)

    def test_circle_view_list_per_page(self):
        """ We can access entries per page """
        self.login()
        response = self.client.get('/dashboard/circles/?page=1')
        self.assertEqual(200, response.status_code)
        response = self.client.get('/dashboard/circles/?page=2')
        self.assertEqual(200, response.status_code)

    def test_circle_view_list_non_exist_page(self):
        """ If we access a *non-existent* page, it should display
            contents from the last page with valid entries
        """
        self.login()
        response = self.client.get('/dashboard/circles/?page=1000')
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Circulo19')


class CircleCrudTests(CircleBaseTestClass):
    """We are testing create/update/delete functionality here."""

    @classmethod
    def setUpClass(cls):
        """ Let's setup our testing workspace"""
        super(CircleCrudTests, cls).setUpClass()
        # Create ordinary contacts
        cls.manuel = models.Contact(imsi='IMSI00101000000000',
                                    callerid='63999000000')

        cls.emilio = models.Contact(imsi='IMSI00101000000001',
                                    callerid='63999000001')
        cls.ramon = models.Contact(imsi='IMSI00101000000002',
                                   callerid='63999000002')
        cls.manuel.save()
        cls.emilio.save()
        cls.ramon.save()

        # Create some circle entries
        cls.bilog = models.Circle(name='Circulo',
                                  description='Dummy text',
                                  owner=cls.admin)
        cls.bilog.save()

        cls.bilogusers1 = models.CircleUsers(circle=cls.bilog,
                                             user=cls.manuel,
                                             date_joined=timezone.now())
        cls.bilogusers2 = models.CircleUsers(circle=cls.bilog,
                                             user=cls.emilio,
                                             date_joined=timezone.now())
        cls.bilogusers1.save()
        cls.bilogusers2.save()

        # Create second circle
        cls.bilog2 = models.Circle(name='Bilog na hugis itlog',
                                   description='Dummy text',
                                   owner=cls.admin)
        cls.bilog2.save()
        cls.bilog2users1 = models.CircleUsers(circle=cls.bilog,
                                              user=cls.ramon,
                                              date_joined=timezone.now())
        cls.bilog2users1.save()

        cls.msg = models.Message(author=cls.admincontact)
        cls.msg.save()

    @classmethod
    def tearDownClass(cls):
        """ Clean them up! """
        super(CircleCrudTests, cls).tearDownClass()
        cls.manuel.delete()
        cls.emilio.delete()
        cls.ramon.delete()
        cls.bilog.delete()
        cls.bilogusers1.delete()
        cls.bilogusers2.delete()
        cls.bilog2.delete()
        cls.bilog2users1.delete()

    def test_create_new_circle(self):
        """We add a new circle by POSTing to /dashboard/circles."""
        self.login()
        # We should start with two circles.
        self.assertEqual(2, models.Circle.objects.all().count())
        data = {
            'name': 'new_circle',
            'users': [self.manuel.pk],
            'description': 'Dummy text'
        }
        self.client.post('/dashboard/circle/new', data)
        # And end up with 3
        self.assertEqual(3, models.Circle.objects.all().count())

    def test_create_new_circle_multiple_users(self):
        """ We add a new circle with multiple members
            by POSTing to /dashboard/circles."""
        self.login()
        # We should start with two circles.
        self.assertEqual(2, models.Circle.objects.all().count())
        data = {
            'name': 'new circle',
            'users': [self.manuel.pk, self.emilio.pk],
            'description': 'Dummy text'
        }
        self.client.post('/dashboard/circle/new', data)
        # And end up with 3
        self.assertEqual(3, models.Circle.objects.all().count())

    def test_create_circle_with_duplicate_name(self):
        """We are not allowed to make circles with duplicate names"""
        self.login()
        # We should start with two circles.
        self.assertEqual(2, models.Circle.objects.all().count())
        data = {
            'name': models.Circle.objects.get(pk=1).name,  # use existing name
            'users': [self.manuel.pk],
            'description': 'Dummy text'
        }
        self.client.post('/dashboard/circle/new', data)
        # The post should fail, we should still end up with 2
        self.assertEqual(2, models.Circle.objects.all().count())

    def test_delete_existing_circle(self):
        """We can delete a circle by POSTing to /dashboard/circles."""
        self.login()
        # We should start with two circles.
        self.assertEqual(2, models.Circle.objects.all().count())
        self.client.post('/dashboard/circle/delete/%s' % self.bilog.pk)
        # And end up with one
        self.assertEqual(1, models.Circle.objects.all().count())

    def test_update_existing_circle(self):
        """We should be able to edit existing circles."""
        self.login()
        data = {
            'name': 'Renamed Circulo',
            'users': [self.manuel.pk, self.emilio.pk],
            'description': 'Dummy text'
        }
        self.client.post('/dashboard/circle/update/%s' % self.bilog.pk, data)
        # Check data in DB to see if params have changed
        circle = models.Circle.objects.get(pk=1)
        circleusers = []
        for item in models.CircleUsers.objects.filter(circle=circle):
            circleusers.append(item.user.imsi)
        self.assertEqual(data['name'], circle.name)
        self.assertEqual(data['users'], circleusers)

    def test_send_broadcast_sms_to_circle(self):
        """We should be able to send a broadcast sms to a circle"""
        self.login()
        send_sms.delay = Mock(return_value=None)
        # We start with 1 message
        self.assertEqual(1, models.Message.objects.all().count())
        url = '/dashboard/circle/broadcast'
        data = {
            'circles': self.bilog.pk,
            'message': 'This is a test message.'
        }
        response = self.client.post(url, data)
        self.assertEqual(200, response.status_code)
        # Check if message count has incremented
        self.assertEqual(2, models.Message.objects.all().count())

    def test_send_broadcast_sms_to_multiple_circles(self):
        """We should be able to send a broadcast sms to multiple circles"""
        self.login()
        send_sms.delay = Mock(return_value=None)
        # We start with 1 message in DB
        self.assertEqual(1, models.Message.objects.all().count())
        url = '/dashboard/circle/broadcast'
        data = {
            'circles': (self.bilog.pk, self.bilog2.pk),
            'message': 'This is a test message.'
        }
        response = self.client.post(url, data)
        self.assertEqual(200, response.status_code)
        # Check if message count has incremented. Sending to multiple circles
        # are lumped as one entry in Messages table
        self.assertEqual(2, models.Message.objects.all().count())
