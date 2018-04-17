"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import mock
from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase

from vbts_webadmin import models
from vbts_webadmin.views import ivrs


class IVRViewTest(TestCase):
    """Testing Ivr UI views"""

    @classmethod
    def setUpClass(cls):
        cls.username = 'Y'
        cls.password = 'YY'
        cls.user = User(username=cls.username, email='X@X.com')
        cls.user.set_password(cls.password)
        cls.user.save()

        cls.test_ivr = models.Ivr(name='myIVR',
                                  number=111,
                                  description='This is a sample IVR.',
                                  code='',
                                  xml_code='')
        cls.test_ivr.save()
        # Create a test client.
        cls.client = Client()

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.test_ivr.delete()

    def login(self):
        """ Logs the client in """
        self.client.login(username=self.username, password=self.password)

    def logout(self):
        """ Logs the client out """
        self.client.logout()

    def tearDown(self):
        """ Make sure we log out the client after every test """
        self.logout()

    def test_ivr_view_list_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        response = self.client.get('/dashboard/ivrs/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/dashboard/ivrs/', follow=True)
        self.assertRedirects(response, '/?next=/dashboard/ivrs/')

    def test_ivr_view_list(self):
        """List down all the IVRs"""
        self.login()
        response = self.client.get('/dashboard/ivrs/')
        self.assertEqual(200, response.status_code)

    def test_ivr_search_random(self):
        """Search a random keyword"""
        self.login()
        keyword = 'random'
        response = self.client.get('/dashboard/ivrs/?search=%s' % keyword)
        self.assertEqual(200, response.status_code)

    def test_ivr_search_random_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        keyword = 'myIVR'
        url = '/dashboard/ivrs/'
        data = {
            'search': keyword
        }
        response = self.client.get(url, data)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, data, follow=True)
        self.assertRedirects(response, '/?next=' + url + '%3Fsearch%3DmyIVR')

    def test_ivr_view_delete(self):
        """ Delete view works """
        self.login()
        url = '/dashboard/ivr/delete/%s' % self.test_ivr.pk
        response = self.client.post(url)
        self.assertEqual(302, response.status_code)  # gets redirected to list

    def test_ivr_view_delete_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/ivr/delete/%s' % self.test_ivr.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_ivr_view_update(self):
        """ Update view works """
        ivrs.load_xml_from_file = mock.Mock(return_value=None)
        ivrs.save_codes = mock.Mock(return_value=None)
        self.login()
        url = '/dashboard/ivr/update/%s' % self.test_ivr.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_ivr_view_update_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        ivrs.load_xml_from_file = mock.Mock(return_value=None)
        ivrs.save_codes = mock.Mock(return_value=None)
        url = '/dashboard/ivr/update/%s' % self.test_ivr.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_ivr_view_detail(self):
        """ Detail view works """
        self.login()
        url = '/dashboard/ivr/view/%s' % self.test_ivr.pk
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_ivr_view_detail_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        url = '/dashboard/ivr/view/%s' % self.test_ivr.pk
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/?next=' + url)

    def test_delete_existing_ivr(self):
        """We can delete an IVR by POSTing to /dashboard/ivr/delete."""
        self.login()
        # We should start with 1 IVR
        self.assertEqual(1, models.Ivr.objects.all().count())
        self.client.post('/dashboard/ivr/delete/%s' % self.test_ivr.pk)
        # And end up with none
        self.assertEqual(0, models.Ivr.objects.all().count())

    def test_delete_non_existing_ivr(self):
        """404 for attempting to access non-existent entries"""
        self.login()
        response = self.client.post('/dashboard/ivr/delete/1000')
        self.assertEqual(404, response.status_code)

    def test_create_new_ivr(self):
        """We should be able to create ivr."""
        ivrs.save_codes = mock.Mock(return_value=None)
        self.login()
        # We should start with 1 IVR
        self.assertEqual(1, models.Ivr.objects.all().count())
        data = {
            'name': 'sample ivr',
            'description': 'This is a sample ivr for our unit test.',
            'number': 111,
            'code': '/tmp/file',
            'xml_code': '/tmp/file'
        }
        self.client.post('/dashboard/ivr/new', data)
        # Check ivr entries in DB increased by 1
        self.assertEqual(2, models.Ivr.objects.all().count())

    def test_create_new_ivr_duplicate_name(self):
        """We should NOT be able to create IVRs with duplicate names."""
        self.login()
        # We should start with 1 IVR
        self.assertEqual(1, models.Ivr.objects.all().count())
        data = {
            'name': self.test_ivr.name,  # same name as init data above
            'description': 'This is a sample ivr for our unit test.',
            'number': 111,
            'code': 'dummy file',
            'xml_code': 'dummy_file'
        }
        self.client.post('/dashboard/ivr/new', data)
        # Count should still be the same
        self.assertEqual(1, models.Ivr.objects.all().count())

    def test_update_existing_ivr(self):
        """We should be able to edit existing IVR."""
        ivrs.load_xml_from_file = mock.Mock(return_value=None)
        ivrs.save_codes = mock.Mock(return_value=None)
        self.login()
        # We should start with 1 IVR
        self.assertEqual(1, models.Ivr.objects.all().count())
        data = {
            'name': 'updated IVR name',
            'description': 'We are updating.',
            'number': 111,
            'code': 'dummy file',
            'xml_code': 'dummy_file'
        }
        self.client.post('/dashboard/ivr/update/%s'
                         % self.test_ivr.pk, data)
        # Check data in DB to see if params have changed
        ivr = models.Ivr.objects.get(pk=self.test_ivr.pk)
        self.assertEqual(data['name'], ivr.name)
        self.assertEqual(data['description'], ivr.description)
