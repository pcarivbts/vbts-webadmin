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


class MessageViewTest(TestCase):

    """Testing Messages UI views"""

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

        # Create ordinary contact
        cls.manuel = models.Contact(imsi='IMSI00101000000000',
                                    callerid='63999000000')
        cls.manuel.save()

        # Create dummy message
        cls.msg = models.Message(author=cls.admincontact,
                                 message='dummy hello message')
        cls.msg.save()

        cls.msg_recv = models.MessageRecipients(message=cls.msg,
                                                user=cls.manuel)
        cls.msg_recv.save()

        # Create a test client.
        cls.client = Client()

    @classmethod
    def tearDownClass(cls):
        """ Clean them up! """
        cls.admin.delete()
        cls.admincontact.delete()
        cls.manuel.delete()
        cls.msg.delete()
        cls.msg_recv.delete()

    def login(self):
        """ Logs the client in """
        self.client.login(username=self.username, password=self.password)

    def logout(self):
        """ Logs the client out """
        self.client.logout()

    def tearDown(self):
        """ Make sure we log out the client after every test """
        self.logout()

    def test_message_view_list_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        response = self.client.get('/dashboard/messages/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/dashboard/messages/', follow=True)
        self.assertRedirects(response, '/?next=/dashboard/messages/')

    def test_message_view_list(self):
        """List down all the messages"""
        self.login()
        response = self.client.get('/dashboard/messages/')
        self.assertEqual(200, response.status_code)

    def test_message_search_random(self):
        """Search a random keyword"""
        self.login()
        keyword = 'random'
        response = self.client.get('/dashboard/messages/?search=%s' % keyword)
        self.assertEqual(200, response.status_code)

    def test_message_search_random_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        keyword = 'random'
        url = '/dashboard/messages/'
        data = {
            'search': keyword
        }
        response = self.client.get(url, data)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, data, follow=True)
        self.assertRedirects(response, '/?next=' + url + '%3Fsearch%3Drandom')

    def test_message_view_detail(self):
        self.login()
        url = '/dashboard/message/view/%s' % self.msg.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_message_view_detail_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/message/view/%s' % self.msg.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_message_view_send(self):
        self.login()
        url = '/dashboard/message/send'
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_message_view_send_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/message/send'
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_send_message(self):
        """We should be able to send an SMS to a subscriber"""
        self.login()
        send_sms.delay = Mock(return_value=None)
        # We start with 1 message
        self.assertEqual(1, models.Message.objects.all().count())
        url = '/dashboard/message/send'
        # query for recipients should have flat=True, to just get imsi value
        data = {
            'recipients': models.Contact.objects.filter(
                callerid='63999000000').values_list('imsi', flat=True),
            'message': 'This is a test message.'
        }
        response = self.client.post(url, data)
        self.assertEqual(200, response.status_code)
        # Check if message count has incremented
        self.assertEqual(2, models.Message.objects.all().count())

    def test_send_messages_multiple_users(self):
        """We should be able to send an sms to a multiple subscribers"""
        self.login()
        send_sms.delay = Mock(return_value=None)
        # We start with 1 message
        self.assertEqual(1, models.Message.objects.all().count())
        url = '/dashboard/message/send'
        # query for recipients should have flat=True, to just get imsi value
        data = {
            'recipients':
                models.Contact.objects.values_list('imsi', flat=True),
            'message': 'This is a test message.'
        }
        response = self.client.post(url, data)
        self.assertEqual(200, response.status_code)
        # Check if message count has incremented
        self.assertEqual(2, models.Message.objects.all().count())
