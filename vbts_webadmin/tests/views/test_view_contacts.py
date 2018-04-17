"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase
from django.utils import timezone
from mock import Mock
from django.db import transaction

from vbts_subscribers_psql.models import Subscribers
from core.subscriber import subscriber
from vbts_webadmin import models


class ContactBaseTestClass(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.username = 'Y'
        cls.password = 'YY'
        cls.user = User(username=cls.username, email='X@X.com')
        cls.user.set_password(cls.password)
        cls.user.save()

        # Create a dummy contact
        cls.manuel = models.Contact(callerid='639990000000',
                                    imsi='IMSI00101000000000')
        cls.manuel.save()

        cls.manuel_profile = models.ContactProfile(
            uuid=1111,
            firstname="Manuel",
            lastname="Roxas",
            nickname="Manu",
            age=30,
            gender='Male',
            municipality='San Luis',
            barangay='Dikapinisan',
            sitio='Dikapinisan Proper'
        )
        cls.manuel_profile.save()

        # NOTE: initial number of contacts is two (2) because the creation of
        # the superuser auto-creates a Contact entry

        # Create a test client.
        cls.client = Client()

        # mock SipBuddies query with none set
        Subscribers.objects.all = Mock(return_value=Subscribers.objects.none())

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.manuel.delete()
        cls.manuel_profile.delete()

    def login(self):
        """ Logs the client in """
        self.client.login(username=self.username, password=self.password)

    def logout(self):
        """ Logs the client out """
        self.client.logout()

    def tearDown(self):
        """ Make sure we log out the client after every test """
        self.logout()

    def test_contact_view_list_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        response = self.client.get('/dashboard/contacts/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/dashboard/contacts/', follow=True)
        self.assertRedirects(response, '/?next=/dashboard/contacts/')

    def test_contact_view_list(self):
        """List down all the contacts"""
        self.login()
        response = self.client.get('/dashboard/contacts/')
        self.assertEqual(200, response.status_code)

    def test_contact_search_random(self):
        """Search a random keyword"""
        self.login()
        keyword = 'random'
        response = self.client.get('/dashboard/contacts/?search=%s' % keyword)
        self.assertEqual(200, response.status_code)

    def test_contact_search_random_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        keyword = 'random'
        url = '/dashboard/contacts/'
        data = {
            'search': keyword
        }
        response = self.client.get(url, data)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, data, follow=True)
        self.assertRedirects(response, '/?next=' + url + '%3Fsearch%3Drandom')

    def test_contact_view_delete(self):
        self.login()
        url = '/dashboard/contacts/delete/%s' % self.manuel_profile.pk
        response = self.client.post(url)
        self.assertEqual(200, response.status_code)

    def test_contact_view_delete_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/contacts/delete/%s' % self.manuel_profile.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_contact_view_update(self):
        self.login()
        url = '/dashboard/contacts/update/%s' % self.manuel_profile.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_contact_view_update_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/contacts/update/%s' % self.manuel_profile.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_contact_view_detail(self):
        self.login()
        url = '/dashboard/contacts/detail/%s' % self.manuel_profile.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_contact_view_detail_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/contacts/detail/%s' % self.manuel_profile.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_contact_view_broadcast_sms_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/contacts/sms'
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_delete_existing_contact(self):
        """We can delete a contact by POSTing to /dashboard/contact/delete."""
        self.login()
        # We should start with 2 contacts
        self.assertEqual(2, models.ContactProfile.objects.all().count())
        self.client.post('/dashboard/contact/delete/%s' %
                         self.manuel_profile.pk)
        # And end up with none
        self.assertEqual(1, models.ContactProfile.objects.all().count())

    def test_delete_non_existing_contact(self):
        """404 for attempting to access non-existent entries"""
        self.login()
        response = self.client.post('/dashboard/contact/delete/1000')
        self.assertEqual(404, response.status_code)

    # def test_create_new_contact(self):
    #     """We should be able to create contact."""
    #     self.login()
    #     # We should start with 2 contacts
    #     self.assertEqual(2, models.ContactProfile.objects.all().count())
    #     data = {
    #         'uuid': 5,
    #         'firstname': 'Gloria',
    #         'lastname': 'Arroyo',
    #         'nickname': 'Glory',
    #         'age': 50,
    #         'gender': 'Female',
    #         'municipality': 'Dingalan',
    #         'barangay': 'Dibut',
    #         'sitio': 'Dibut Proper'
    #     }
    #     resp = self.client.post('/dashboard/contact/new', data)
    #     # Check contact entries in DB increased by 1
    #     self.assertEqual(3, models.ContactProfile.objects.all().count())

    def test_create_new_contact_duplicate_uuid(self):
        """We should NOT be able to create contacts with duplicate names."""
        self.login()
        # We should start with 2 contacts
        self.assertEqual(2, models.ContactProfile.objects.all().count())
        data = {
            'uuid': 1111,
            'firstname': 'Gloria',
            'lastname': 'Arroyo',
            'nickname': 'Glory',
            'age': 50,
            'gender': 'Female',
            'municipality': 'Dingalan',
            'barangay': 'Dibut',
            'sitio': 'Dibut Proper'
        }
        self.client.post('/dashboard/contact/new', data)
        # Count should still be the same
        self.assertEqual(2, models.Contact.objects.all().count())

    # def test_update_existing_contact(self):
    #     """We should be able to edit existing contact."""
    #     self.login()
    #     # We should start with 2 contacts
    #     self.assertEqual(2, models.ContactProfile.objects.all().count())
    #     data = {
    #         'firstname': 'Manuel',
    #         'lastname': 'Roxas',
    #         'age': 50,
    #         'municipality': 'Dingalan'
    #     }
    #     self.client.post('/dashboard/contact/update/%s'
    #                      % self.manuel_profile.id, data)
    #     # Check data in DB to see if params have changed
    #     contact = models.ContactProfile.objects.get(pk=self.manuel_profile.pk)
    #     self.assertEqual(data['lastname'], contact.lastname)
    #     self.assertEqual(data['municipality'], contact.municipality)
    #     # contacts should still be 2
    #     self.assertEqual(2, models.ContactProfile.objects.all().count())
