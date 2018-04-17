"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.

-
Sets up a a basic test DB for external (non-test suite) testing.

Adds Admin, Circles, Groups, Services, Subscribers -- all this should then
be visible in a local dashboard.  Make sure you've first properly
setup the db and its migrations.  Then you can login with the test
username and pw as defined below.

Usage:
    python manage.py setup_test_db

To reset the local test db:
    python manage.py flush
    python manage.py migrate vbts_webadmin
    python manage.py migrate authtoken
"""

import time
from django.core.management.base import BaseCommand
from vbts_subscribers.models import SipBuddies


class Command(BaseCommand):
    help = 'Adds a contiguous number block to the DB.'

    def add_arguments(self, parser):
        parser.add_argument('start_imsi', type=str)
        parser.add_argument('start_callerid', type=int)
        parser.add_argument('block_size', type=int)

    def handle(self, *args, **options):
        start_imsi = options['start_imsi']
        start_callerid = options['start_callerid']
        block_size = options['block_size']

        for i in range(0, block_size):
            imsi = '%s%02d' % (start_imsi, i)
            callerid = '%s' % (start_callerid + i)
            balance = i * 20
            regtime = time.time()
            self.reg_subscriber(imsi, callerid, balance, regtime)
            print (("Added %s - %s -%d - %f to DB.") %
                   (imsi, callerid, balance, regtime))

    def reg_subscriber(self, imsi, callerid, balance, regtime):
        buddy = SipBuddies(name=imsi,
                           callerid=callerid,
                           account_balance=balance,
                           regtime=regtime)
        buddy.save()
