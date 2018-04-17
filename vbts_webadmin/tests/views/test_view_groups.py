"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import random

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase

from vbts_webadmin import models


class GroupsBaseTestClass(TestCase):
    """Base class for testing Groups UI views"""

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


class GroupViewTest(GroupsBaseTestClass):
    """Testing Groups UI views"""

    def test_group_view_list_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        response = self.client.get('/dashboard/groups/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/dashboard/groups/', follow=True)
        self.assertRedirects(response, '/?next=/dashboard/groups/')

    def test_group_view_list(self):
        """List down all the groups"""
        self.login()
        response = self.client.get('/dashboard/groups/')
        self.assertEqual(200, response.status_code)

    def test_group_search_random(self):
        """Search a random keyword"""
        self.login()
        keyword = 'random'
        response = self.client.get('/dashboard/groups/?search=%s' % keyword)
        self.assertEqual(200, response.status_code)

    def test_group_search_random_sans_auth(self):
        """ We are not logged in, so we should be redirected """
        keyword = 'random'
        url = '/dashboard/groups/'
        data = {
            'search': keyword
        }
        response = self.client.get(url, data)
        self.assertEqual(302, response.status_code)
        response = self.client.get(url, data, follow=True)
        self.assertRedirects(response, '/?next=' + url + '%3Fsearch%3Drandom')


class GroupsEmptyList(GroupsBaseTestClass):
    """Testing pagination for empty group list"""

    def test_group_view_list_empty(self):
        """Go to the empty list"""
        self.login()
        response = self.client.get('/dashboard/groups/')
        self.assertEqual(200, response.status_code)


class GroupsLongList(GroupsBaseTestClass):
    """Testing pagination for *long* group list"""

    @classmethod
    def setUpClass(cls):
        super(GroupsLongList, cls).setUpClass()
        for i in xrange(0, 20):
            models.Group.objects.create(name='Group%d' % i,
                                        owner=cls.admincontact)

    @classmethod
    def tearDownClass(cls):
        super(GroupsLongList, cls).tearDownClass()
        models.Group.objects.all().delete()

    def test_group_view_list_long(self):
        """List down all the groups"""
        self.login()
        response = self.client.get('/dashboard/groups/')
        self.assertEqual(200, response.status_code)

    def test_group_view_list_per_page(self):
        """ We can access entries per page """
        self.login()
        response = self.client.get('/dashboard/groups/?page=1')
        self.assertEqual(200, response.status_code)
        response = self.client.get('/dashboard/groups/?page=2')
        self.assertEqual(200, response.status_code)

    def test_group_view_list_non_exist_page(self):
        """ If we access a *non-existent* page, it should display
            contents from the last page with valid entries
        """
        self.login()
        response = self.client.get('/dashboard/groups/?page=1000')
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Group19')

    def test_group_view_detail(self):
        """View the detail of a specific group"""
        self.login()
        pk = random.randint(1, 20)
        response = self.client.get('/dashboard/group/view/%d' % pk)
        self.assertEqual(200, response.status_code)
