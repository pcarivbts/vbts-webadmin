"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import absolute_import

from os import system
import subprocess

from celery.decorators import periodic_task
from celery.task.schedules import crontab

from vbts_webadmin.celery import app
from vbts_webadmin.models import PromoSubscription
from vbts_webadmin.models import Service
from vbts_webadmin.models import ServiceSubscribers
from vbts_webadmin.models import ServiceEvents
from vbts_webadmin.utils import msg_chop
from core.subscriber import subscriber as endaga_sub

from core import events
from core.config_database import ConfigDB
from core.freeswitch_interconnect import freeswitch_ic


@app.task()
def test_me():
    from time import gmtime, strftime
    timenow = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    with open("~/testcelery.txt", "a") as myfile:
        myfile.write(timenow)


def test(param):
    return 'The test task executed with argument "%s" ' % param


@app.task()
def send_sms(callerid, origin, msg, as_list=False):
    """
        Sends SMS to subscriber
    Args:
        callerid: callerid of subscriber
        origin: sender's callerid
        msg: message to be sent
        as_list: True if data passed is a list data type

    Returns: None

    """
    # FIXME: can't use the commented lines below because celery kills the DB
    # FIXME: connection, complains 'InterfaceError: connection already closed'
    # fs_con = freeswitch_ic(ConfigDB())
    # fs_con.send_to_number(callerid, '0000', msg)
    # FIXME: use this for the meantime

    if as_list:
        blocks = msg
    else:
        blocks = msg_chop(msg)

    for item in blocks:
        cmd = "fs_cli -x \"python VBTS_Send_SMS %s|%s|%s\" " % (
            callerid, origin, item.replace('"', '\\"'))
        system(cmd)


@app.task()
def purge_entry(pk):
    """
        Once a subscriber's promo subscription expires, this task will remove
        the entry from pcari_promo_subscriptions table
        Also, it sends an SMS to inform the subscriber that the
        promo has expired
    Args:
        pk: primary key of PromoSubscriptions entry

    Returns: None
    """

    subscription = PromoSubscription.objects.get(pk=pk)
    promoname = subscription.promo.keyword
    callerid = subscription.contact.callerid

    # we should also create an event
    balance = endaga_sub.get_account_balance(subscription.contact.imsi)
    reason = "Promo Expiration: %s" % subscription.promo.keyword
    events.create_sms_event(subscription.contact.imsi, balance,
                            0, reason, '555')

    subscription.delete()

    # inform user that promo has expired
    msg = "Your %s promo subscription has already expired." % promoname
    send_sms(callerid, '0000', msg)


@app.task()
def reload_fs_xml():
    cmd = "fs_cli -x 'reloadxml' "
    system(cmd)


@app.task()
def push_cmd_routine(service_pk):
    """
        For push-based services, this handles content delivery to subscribers
    Args:
        service_pk: primary key of the service i
    Returns:
        None
    """
    # Execute code defined by service.scripts or service.plugin
    # and then get result

    try:
        subscriptions = ServiceSubscribers.objects.filter(service=service_pk)
        service = Service.objects.get(pk=service_pk)
        # cmd = "fs_cli -x 'python %s %s' " % (service.script.fs_script,
        #                                      service.script_arguments.value)
        # result = subprocess.check_output(cmd, shell=True)
        result = 'You received a dummy output.'
        for item in subscriptions:
            # Check balance of subscriber first
            balance = endaga_sub.get_account_balance(item.subscriber.imsi)
            if balance - item.service.price < 0:
                # not enough balance, TODO: determine proper action here
                pass
            else:
                send_sms.delay(item.subscriber.callerid, '0000', result)
                endaga_sub.subtract_credit(item.subscriber.imsi,
                                           str(item.service.price))
                event = "Received pushed content from '%s' service" % \
                        item.service.keyword
                ServiceEvents.objects.create(service=item.service,
                                             subscriber=item.subscriber,
                                             event=event)
    except BaseException:
        pass
        # no subscribers, nothing to do.
    return result
