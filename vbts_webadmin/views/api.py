"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from datetime import timedelta

from core import billing
from core import events
from core import number_utilities
from core.subscriber import subscriber as endaga_sub
from django.db.models import Q
from django.utils import timezone as timezone
from django.utils.translation import ugettext as _
from pytz import timezone as pytz_timezone
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from vbts_webadmin.celery import app
from vbts_webadmin.models import Config
from vbts_webadmin.models import Contact
from vbts_webadmin.models import Group
from vbts_webadmin.models import GroupMembers
from vbts_webadmin.models import Message
from vbts_webadmin.models import MessageRecipients
from vbts_webadmin.models import Promo
from vbts_webadmin.models import PromoSubscription
from vbts_webadmin.models import Report
from vbts_webadmin.models import ReportMessages
from vbts_webadmin.models import Service
from vbts_webadmin.models import ServiceEvents
from vbts_webadmin.models import ServiceSubscribers
from vbts_webadmin.renderers import PlainTextRenderer
from vbts_webadmin.tasks import purge_entry
from vbts_webadmin.tasks import send_sms
from vbts_webadmin.utils import mc_to_float


class CreateContact(APIView):
    """
        User wanted to register
        <base_url>/api/contact?
        Data arguments:
            imsi:   IMSI of user
            callerid:   Callerid of user
            lastname:   *required
            firstname:  *required
            birthdate: MM/DD/YYYY
            address:
    """

    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request):
        """ POST method for registering contact """

        needed_fields = ["imsi", "callerid"]
        # needed_fields = ["imsi", "callerid", "lastname", "firstname"]
        if all(i in request.POST for i in needed_fields):

            # if it is not in args, let's replace with dummy data
            fields = ['firstname', 'lastname', 'birthdate', 'address']
            dummy = ['User', request.data['callerid'], timezone.now(),
                     'Diliman, QC']
            # for i in xrange(0, len(fields)):
            #    if fields[i] not in request.data:
            #        request.data[fields[i]] = dummy[i]

            new_contact = Contact()
            new_contact.imsi = request.data['imsi']
            new_contact.callerid = request.data['callerid']
            new_contact.save()

            send_sms.delay(request.data['callerid'], '0000',
                           _("You are now listed in the VBTS database."))

            return Response('OK CREATED', status=status.HTTP_200_OK)

        return Response("ERROR", status=status.HTTP_400_BAD_REQUEST)


class SubmitReport(APIView):
    """ Create a report
        <base_url>/api/report/submit/?
        Data arguments:
            imsi:       IMSI of reporter
            keyword:    *required
            message:    *required
    """

    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request):
        """ POST method for submitting a report """
        needed_fields = ["imsi", "keyword", "message"]
        if not all(i in request.POST for i in needed_fields):
            return Response("ERROR: Missing arguments.",
                            status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        try:
            subscriber = Contact.objects.get(imsi__exact=imsi)
        except BaseException:
            send_sms.delay(endaga_sub.get_numbers_from_imsi(imsi)[0], '0000',
                           _("You are currently not registered to the BTS. "
                             "Please register."))
            return Response("ERROR: Not registered subscriber.",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            report = Report.objects.filter(
                Q(keyword=request.data['keyword'].upper()) &
                Q(status='P'))[0]
        except BaseException:
            send_sms.delay(subscriber.callerid, '0000',
                           _("Sorry we can't process your request. "
                             "Invalid keyword."))
            return Response("ERROR: Invalid keyword.",
                            status=status.HTTP_400_BAD_REQUEST)

        new_report = ReportMessages()
        new_report.sender = subscriber
        new_report.report = report
        new_report.message = request.data['message']
        new_report.date = timezone.now()
        new_report.save()

        send_sms.delay(subscriber.callerid, '0000',
                       _("You have successfully sent a report to %s.")
                       % report.keyword)
        for manager in report.managers.all():
            send_sms.delay(manager.callerid, '0000',
                           _("New report from %(manager)s. "
                             "%(keyword)s:%(msg)s") % ({
                                 'manager': manager.callerid,
                                 'keyword': report.keyword,
                                 'msg': new_report.message
                             }))

        return Response('OK CREATED', status=status.HTTP_200_OK)


class SubscribeToService(APIView):
    """ Subscribe to a service.
        <base_url>/api/service/subscribe/?
        Data arguments:
            imsi:   IMSI of subscriber
            keyword: Keyword of service  *required
    """

    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request):
        """ POST method for subscribing to a service """
        needed_fields = ["imsi", "keyword"]
        if not all(i in request.POST for i in needed_fields):
            return Response("ERROR: Missing arguments.",
                            status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']

        try:
            subscriber = Contact.objects.get(imsi__exact=imsi)
        except BaseException:
            send_sms.delay(endaga_sub.get_numbers_from_imsi(imsi)[0], '0000',
                           _("You are currently not registered to the BTS. "
                             "Please register."))
            return Response("ERROR: Not registered subscriber.",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            service = Service.objects.filter(
                keyword=request.data['keyword'].upper(),
                service_type='P', status='P')[0]
        except BaseException:
            send_sms.delay(subscriber.callerid, '0000',
                           _("Sorry we can't process your request. "
                             "Invalid keyword."))
            return Response("ERROR: Invalid keyword.",
                            status=status.HTTP_400_BAD_REQUEST)

        is_duplicate = ServiceSubscribers.objects. \
            filter(service=service, subscriber=subscriber).exists()

        if is_duplicate:
            send_sms.delay(
                subscriber.callerid,
                '0000',
                _("You are already subscribed to %s.") %
                service.name)
            return Response('OK ALREADY SUBSCRIBED', status=status.HTTP_200_OK)

        else:
            # check if subscriber has enough balance
            balance = endaga_sub.get_account_balance(imsi)
            if balance - service.price < 0:
                send_sms.delay(subscriber.callerid, '0000',
                               _("You do not have sufficient balance to "
                                 "subscribe to %s.") % service.name)
                return Response("Insufficient balance",
                                status=status.HTTP_402_PAYMENT_REQUIRED)

            # user passes above check, has enough balance, so sign him up!
            new_subscription = ServiceSubscribers(subscriber=subscriber,
                                                  service=service)
            new_subscription.date_joined = timezone.now()
            new_subscription.save()
            # finally, deduct service.price from subscriber's balance
            # price is expressed in millicents
            endaga_sub.subtract_credit(imsi, str(service.price))

            send_sms.delay(subscriber.callerid, '0000',
                           _("You have successfully subscribed to %s.")
                           % service.name)
            return Response('OK SUBSCRIBED', status=status.HTTP_200_OK)


class UnsubscribeToService(APIView):
    """ Unsubscribe to a service.
        <base_url>/api/service/unsubscribe/?
        Data arguments:
            imsi:   IMSI of subscriber
            keyword:  Keyword of service *required
    """

    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request):
        """ POST method for opting out from a service """
        needed_fields = ["imsi", "keyword"]
        if not all(i in request.POST for i in needed_fields):
            return Response("ERROR: Missing arguments.",
                            status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        keyword = request.data['keyword']

        try:
            subscriber = Contact.objects.get(imsi__exact=imsi)
        except BaseException:
            send_sms.delay(endaga_sub.get_numbers_from_imsi(imsi)[0], '0000',
                           _("You are currently not registered to the BTS. "
                             "Please register."))
            return Response("ERROR: Not registered subscriber.",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription = ServiceSubscribers.objects.filter(
                service__keyword__exact=keyword,
                subscriber__imsi__exact=request.data['imsi'])[0]
            subscription.delete()
            send_sms.delay(subscriber.callerid, '0000',
                           _("You have successfully unsubscribed to %s.")
                           % subscription.service.name)
            return Response('OK UNSUBSCRIBED', status=status.HTTP_200_OK)
        except BaseException:
            send_sms.delay(subscriber.callerid, '0000', _(
                "You are not currently subscribed to the service."))
            return Response("ERROR: You are not currently subscribed to "
                            "the %s service." % keyword,
                            status=status.HTTP_400_BAD_REQUEST)


class GetServiceStatus(APIView):
    """ Get the subscriber's status for a particular service
        <base_url>/api/service/status/?
        Data arguments:
            imsi:   IMSI of subscriber
            keyword: Keyword of service  *required
    """

    renderer_classes = (JSONRenderer,)

    def post(self, request):
        """ POST method for subscribing to a service """
        needed_fields = ["imsi", "keyword"]
        if not all(i in request.POST for i in needed_fields):
            return Response("ERROR: Missing arguments.",
                            status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']

        try:
            subscriber = Contact.objects.get(imsi__exact=imsi)
        except BaseException:
            send_sms.delay(endaga_sub.get_numbers_from_imsi(imsi)[0], '0000',
                           _("You are currently not registered to the BTS. "
                             "Please register."))
            return Response("ERROR: Not registered subscriber.",
                            status=status.HTTP_404_NOT_FOUND)

        try:
            service = Service.objects.filter(
                keyword=request.data['keyword'].upper(),
                service_type='P', status='P')[0]
        except BaseException:
            send_sms.delay(subscriber.callerid, '0000',
                           _("Sorry we can't process your request. "
                             "Invalid keyword."))
            return Response("ERROR: Invalid keyword.",
                            status=status.HTTP_400_BAD_REQUEST)

        is_subscribed = ServiceSubscribers.objects. \
            filter(service=service, subscriber=subscriber).exists()

        if is_subscribed:
            send_sms.delay(subscriber.callerid, '0000',
                           _("You are subscribed to %s.") % service.name)
            return Response('OK STATUS - SUBSCRIBED',
                            status=status.HTTP_200_OK)

        else:
            send_sms.delay(subscriber.callerid, '0000',
                           _("You are not subscribed to %s.")
                           % service.name)
            return Response('OK STATUS - NOT SUBSCRIBED',
                            status=status.HTTP_200_OK)


class GetLocalServicePrice(APIView):
    """ Get the rate/price for a particular local service
        <base_url>/api/service/price/?
        Data arguments:
            keyword: Keyword of service  *required
    """

    renderer_classes = (JSONRenderer,)

    def post(self, request):
        if "keyword" not in request.POST:
            return Response("ERROR: Missing arguments.",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            price = Service.objects.get(
                keyword=request.POST['keyword'].upper()).price
        except BaseException:
            price = 0
        return Response(price, status=status.HTTP_200_OK)


class CreateServiceEvent(APIView):
    """ Creates a Service Event Entry
        <base_url>/api/service/event/?
        Data arguments:
            keyword: Keyword of service  *required
            imsi: subscriber's imsi
    """

    renderer_classes = (JSONRenderer,)

    def post(self, request):
        needed_fields = ["imsi", "keyword"]
        if not all(i in request.POST for i in needed_fields):
            return Response("ERROR: Missing arguments.",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            service = Service.objects.get(keyword=request.POST['keyword'])
            subscriber = Contact.objects.get(imsi=request.POST['imsi'])
        except BaseException:
            return Response('BAD ARGS', status=status.HTTP_400_BAD_REQUEST)

        try:
            event = "Sent info request to '%s' service" % service.keyword
            ServiceEvents.objects.create(service=service,
                                         subscriber=subscriber,
                                         event=event)
            return Response('OK EVENT', status=status.HTTP_200_OK)
        except BaseException:
            return Response('ERROR CREATING EVENT',
                            status=status.HTTP_400_BAD_REQUEST)


class SendSubscribersMsg(APIView):
    """ Send message to service's subscribers.
        <base_url>/api/service/send/?
        Data arguments:
            imsi:   IMSI of sender
            keyword: Keyword of service *required
            message: Message
    """

    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request):
        """ POST method to send message to service's subscribers. """
        needed_fields = ["imsi", "keyword", "message"]
        if not all(i in request.POST for i in needed_fields):
            return Response("ERROR: Missing arguments.",
                            status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        keyword = request.data['keyword']
        try:
            service = Service.objects.filter(keyword=keyword.upper(),
                                             status='P')[0]
        except BaseException:
            send_sms.delay(endaga_sub.get_numbers_from_imsi(imsi)[0], '0000',
                           _("Sorry we can't process your request. "
                             "Invalid service."))
            return Response("ERROR: Invalid service.",
                            status=status.HTTP_400_BAD_REQUEST)

        # check first if sender is the service manager
        # if so, propagate message to all service subscribers
        if service.managers.filter(imsi=request.data['imsi']).exists():
            for subscriber in service.subscribers.all():
                send_sms.delay(subscriber.callerid, '0000',
                               _("ANNOUNCEMENT: %s") % request.data['message'])
            return Response('ANNOUNCEMENT SENT', status=status.HTTP_200_OK)

        else:
            send_sms.delay(endaga_sub.get_numbers_from_imsi(imsi)[0], '0000',
                           _("You are not allowed to send message to %s's "
                             "subscribers.") % keyword)
            return Response("ERROR: No administrative privileges to send to "
                            "this %s's subscribers."
                            % keyword, status=status.HTTP_400_BAD_REQUEST)


class PromoSubscribe(APIView):
    """ Subscribe to a promo
        <base_url>/api/promo/subscribe?
        Data arguments:
            imsi:       IMSI
            keyword:    keyword of the promo to be availed
    """

    # Remove this for the meantime
    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request):
        needed_fields = ["imsi", "keyword"]
        if not all(i in request.POST for i in needed_fields):
            return Response("Missing Args", status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        keyword = request.data['keyword']

        try:
            subscriber = Contact.objects.get(imsi__exact=imsi)
        except BaseException:  # subscriber not found in Contacts table
            send_sms.delay(endaga_sub.get_numbers_from_imsi(imsi)[0], '0000',
                           _("You are not listed in the PCARI-VBTS database. "
                             "Please register."))
            return Response("Not Found", status=status.HTTP_404_NOT_FOUND)

        # We put code to optionally limit promo subscriptions
        # this depends on the limit type declared in the configs

        try:
            limit_type = Config.objects.get(key='promo_limit_type').value
        except Config.DoesNotExist:
            limit_type = 'NA'

        try:
            max_promo_subscription = int(Config.objects.get(
                key='max_promo_subscription').value)
        except Config.DoesNotExist:
            max_promo_subscription = 1

        try:
            min_balance_required = float(Config.objects.get(
                key='min_balance_required').value)
        except Config.DoesNotExist:
            min_balance_required = 0

        # type A: Limit number of subscription per promo
        if limit_type == 'A':
            count = PromoSubscription.objects.filter(
                promo__keyword__exact=keyword, contact=subscriber).count()
            if count >= max_promo_subscription:
                send_sms.delay(subscriber.callerid, '0000',
                               _("You have to many promo subscriptions."))
                return Response("Too Many Subscriptions",
                                status=status.HTTP_403_FORBIDDEN)

        # type B: Limit number of subscription for all promos
        elif limit_type == 'B':
            count = PromoSubscription.objects.filter(
                contact=subscriber).count()
            if count >= max_promo_subscription:
                send_sms.delay(subscriber.callerid, '0000',
                               _("You have to many promo subscriptions."))
                return Response("Too Many Subscriptions",
                                status=status.HTTP_403_FORBIDDEN)
        else:
            pass  # proceed as usual

        try:
            promo = Promo.objects.get(keyword__exact=keyword)
        except BaseException:  # bad promo keyword
            send_sms.delay(subscriber.callerid, '0000',
                           _("You made a bad promo request."))
            return Response("Bad promo request",
                            status=status.HTTP_400_BAD_REQUEST)

        # check account balance first
        balance = endaga_sub.get_account_balance(imsi)
        if balance - promo.price < min_balance_required:
            send_sms.delay(subscriber.callerid, '0000',
                           _("You do not have sufficient balance to subscribe "
                             "to the %s promo.") % promo.keyword)
            return Response("Insufficient balance",
                            status=status.HTTP_402_PAYMENT_REQUIRED)

        # user passes above check, has enough balance, so sign him up!
        new_subscription = PromoSubscription()
        new_subscription.promo = promo
        new_subscription.contact = subscriber
        # save time as UTC in database
        new_subscription.date_expiration = timezone.now() + timedelta(
            promo.validity)
        new_subscription.local_sms = promo.local_sms
        new_subscription.local_call = promo.local_call
        new_subscription.globe_sms = promo.globe_sms
        new_subscription.globe_call = promo.globe_call
        new_subscription.outside_sms = promo.outside_sms
        new_subscription.outside_call = promo.outside_call
        new_subscription.save()

        # finally, deduct promo.price from subscriber's balance
        # price is expressed in millicents
        endaga_sub.subtract_credit(imsi, str(promo.price))

        try:
            tz = Config.objects.get(key='timezone').value
        except Config.DoesNotExist:
            tz = pytz_timezone('Asia/Manila')

        # present time to subscriber according to defined timezone
        expiry = new_subscription.date_expiration.astimezone(tz). \
            strftime("%m/%d/%y %I:%M%p")

        # and then lets inform the subscriber
        send_sms.delay(subscriber.callerid, '0000',
                       _("You are now subscribed to %(keyword)s valid "
                         "until %(expiry)s.") % ({
                             'keyword': promo.keyword,
                             'expiry': expiry
                         }))

        # and then create a purge task
        # let's use the PK as the task_id, so that we dont have to create
        # a new field to store the id. this might be OK for now.
        purge_entry.apply_async(eta=new_subscription.date_expiration,
                                args=[new_subscription.pk],
                                task_id=str(new_subscription.pk))

        # we should also create an event
        reason = "Promo subscription: %s" % promo.keyword
        events.create_sms_event(subscriber.imsi, balance,
                                promo.price, reason, '555')

        return Response('OK SUBSCRIBE', status=status.HTTP_200_OK)


def is_dest_globe(dest):
    prefix_globe = [
        '63905',
        '63906',
        '63915',
        '63916',
        '63917',
        '63926',
        '63927',
        '63935',
        '63945',
        '63955',
        '63956',
        '63966',
        '63975',
        '63976',
        '63977',
        '63995',
        '63997',
    ]

    prefix_globe_abscbn = ['63937']

    prefix_globe_cherry = ['63996']

    prefix_tmbrgy = ['63936']

    if dest[:5] in prefix_globe + prefix_globe_abscbn + \
            prefix_globe_cherry + prefix_tmbrgy:
        return True
    else:
        return False


class GetServiceType(APIView):
    """ Checks how the subscriber should be charged based on their
        transaction (call or sms) and their promo quotas
        Data Args:
            imsi: imsi of subscriber
            trans: either 'local_call', 'outside call',
                        'local_sms', 'outside_sms'
            dest: destination callerid
        Output:
            charging_type: either [U_, B_, D_, G_] + [local, outside]
            + [call, sms]
    """

    renderer_classes = (PlainTextRenderer,)

    def post(self, request, format=None):
        needed_fields = ["imsi", "trans", "dest"]
        if not all(i in request.POST for i in needed_fields):
            return Response("Missing Args", status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        ret = transaction = request.data['trans']
        dest = request.data['dest']

        # Kludge!
        try:
            endaga_sub.get_imsi_from_number(dest)
            local = True
        except BaseException:
            local = False

        if not local and is_dest_globe(dest):
            # replace first word with globe keyword
            transaction = 'globe_' + transaction.split('_')[1]

        # check first if subscriber has subscribed to U/B/D promos
        # follows priority order

        # we also have to check that the subscriber has allocation
        # for the transaction. For example: if a user wants to do
        # outside sms but only has promo allocation for unli local sms, then
        # we should apply regular rates
        for promo_type in ['U', 'B', 'D', 'G']:
            query = transaction + '__gt'
            listed_promos = PromoSubscription.objects.filter(
                contact__imsi__exact=imsi, promo__promo_type=promo_type,
                **{query: 0}).order_by('date_expiration')
            if listed_promos:
                if promo_type == 'G':  # check destination number
                    try:
                        GroupMembers.objects.get(group__owner__exact=imsi,
                                                 user__callerid=dest)
                        break
                    except BaseException:
                        pass  # destination not a group member, do nothing
                else:
                    break
        # No promo subscriptions
        else:
            return Response(ret, status=status.HTTP_200_OK)

        # NOTE: get the first item from queryset since that would expire first
        key = 'listed_promos[0].%s' % transaction
        if eval(key) > 0:
            ret = '%s_%s' % (promo_type, transaction)

        return Response(ret, status=status.HTTP_200_OK)


class GetRequiredBalance(APIView):
    """
        <base_url>/api/promo/getminbal?
        Get the required minimum balance depending on transaction
        If the transaction will fall under promo, then we impose that
        a subscriber should at least have a '1' peso account balance
        Otherwise, min balance would be the same as reg call tariff
        Data Args:
            trans: transaction type, any of the ff combinations
                   ['U', 'B', 'D', 'G', ''] + ['local', 'outside']
                   + ['call', 'sms']
                   example: 'local_call', 'U_local_call'
            tariff: exisiting call_tariff, as returned by VBTS_Get_Call_Tariff
        Output:
            min_bal: minimum balance required
    """

    renderer_classes = (PlainTextRenderer,)

    def post(self, request, format=None):
        needed_fields = ["trans", "tariff"]
        if not all(i in request.POST for i in needed_fields):
            return Response("Missing Args", status=status.HTTP_400_BAD_REQUEST)

        if 'U_' in request.data['trans'] or 'B_' in request.data['trans']:
            # at least 1 peso required to use promo quotas
            try:
                min_bal = Config.objects.get(key='promo_req_min_balance').value
            except Config.DoesNotExist:
                min_bal = '0'
        # apply existing tariff for regular or discounted types
        else:
            min_bal = request.data['tariff']

        return Response(min_bal, status=status.HTTP_200_OK)


def extract_types(transaction):
    """
        Extracts promo_type and service_type
    Args:
        transaction: input from FS chatplan

    Returns:
        promo_type: either U, B, D, G
        service_type: either [local, outside] + [call, sms]

    """
    needed_fields = ['U_', 'B_', 'D_', 'G_']
    if transaction[:2] in needed_fields:
        promo_type = transaction[:1]
        service_type = transaction[2:]
    else:
        service_type = transaction
        promo_type = ''

    return promo_type, service_type


class GetServiceTariff(APIView):
    """
        <base_url>/api/promo/getservicetariff?
        Gets service tariff applicable for given service_type and
        target destination, if applicable
        Data Args:
            imsi: subcriber's IMSI
            trans: either [U_, B_, D_, G_] + [local, outside] + [call, sms]
            dest: destination number, can be empty if local
    """
    renderer_classes = (PlainTextRenderer,)

    def post(self, request, format=None):
        needed_fields = ["imsi", "trans", "dest"]
        if not all(i in request.POST for i in needed_fields):
            return Response("Missing Args", status=status.HTTP_400_BAD_REQUEST)

        promo_type, service_type = extract_types(request.data['trans'])
        imsi = request.data['imsi']
        dest = request.data['dest']

        # Assume first that regular tariffs will be applied
        # then overwrite later if promos apply.
        # Kinda weird, but this avoid 'ret' being unset if Disc
        # promo is suddenly purged by celery while traversing FS dialplan
        if 'sms' in service_type:
            call_or_sms = 'sms'
        else:
            call_or_sms = 'call'
        destination_number = number_utilities.strip_number(dest)

        # Kludge!
        if 'globe' in service_type:
            # replace first word with globe keyword
            ret = str(billing.get_service_tariff(
                'outside_' + service_type.split('_')[1],
                call_or_sms,
                destination_number)
            )
        else:
            ret = str(billing.get_service_tariff(
                service_type,
                call_or_sms,
                destination_number)
            )

        # if unli or bulk, no tariff
        if promo_type == 'U' or promo_type == 'B':
            ret = '0'

        # if discounted, get tariff from earliest subscribed discounted promo
        elif promo_type in ['D']:
            query = service_type + '__gt'
            promo = PromoSubscription.objects.filter(
                contact__imsi__exact=imsi, promo__promo_type=promo_type,
                **{query: 0}).order_by('date_expiration')

            if promo:
                key = 'promo[0].%s' % service_type
                ret = str(eval(key))
                # else, regular tariffs from above will apply

        elif promo_type in ['G']:
            query = service_type + '__gt'
            promo = PromoSubscription.objects.filter(
                contact__imsi__exact=imsi, promo__promo_type=promo_type,
                **{query: 0}).order_by('date_expiration')
            member = GroupMembers.objects.filter(
                group__owner__imsi__exact=imsi, user__callerid__exact=dest)

            if promo and member:
                key = 'promo[0].%s' % service_type
                ret = str(eval(key))
                # else, regular tariffs from above will apply

        return Response(ret, status=status.HTTP_200_OK)


class GetSecAvail(APIView):
    """
        Gets to number of available seconds that a subscriber can use to call
        For promo types, max is configurable, default is 180 seconds
    Data Args:
        imsi:   subscriber IMSI
        trans:  refers to service_type,
                either [U_, B_, D_, G_] + [local, outside] + [call]
        balance: balance passed by FS dialplan, expressed in millicents
        dest:   the destination number, if applicable
    """
    renderer_classes = (PlainTextRenderer,)

    def post(self, request, format=None):
        needed_fields = ["imsi", "trans", "balance", "dest"]
        if not all(i in request.POST for i in needed_fields):
            return Response("Missing Args", status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        promo_type, service_type = extract_types(request.data['trans'])
        balance = int(request.data['balance'])
        dest = request.data['dest']

        destination_number = number_utilities.strip_number(dest)

        # This is the number of seconds available
        # based on the subs current balance
        if 'globe' in service_type:
            # replace first word with globe keyword
            sec_avail = int(billing.get_seconds_available(
                            int(balance),
                            'outside_' + service_type.split('_')[1],
                            destination_number)
                            )

        else:
            sec_avail = int(billing.get_seconds_available(
                            int(balance),
                            service_type,
                            destination_number))

        try:
            max_call_duration = Config.objects.get(
                key='max_call_duration').value
            if int(max_call_duration) <= 0:
                raise ValueError
        except (Config.DoesNotExist, ValueError):
            # cap call at 1-day duration limit
            max_call_duration = 24 * 60 * 60

        # if unli, no tariff
        if promo_type == 'U':
            sec_avail = max_call_duration

        # if bulk, depends on remaining quota
        elif promo_type == 'B':
            query = service_type + '__gt'
            promo = PromoSubscription.objects.filter(
                contact__imsi__exact=imsi, promo__promo_type=promo_type,
                **{query: 0}).order_by('date_expiration')
            if promo:
                key = 'promo[0].%s' % service_type
                sec_avail = eval(key) * 60

        # if discounted, get tariff from earliest subscribed discounted promo
        elif promo_type in ['D', 'G']:
            query = service_type + '__gt'
            promo = PromoSubscription.objects.filter(
                contact__imsi__exact=imsi, promo__promo_type=promo_type,
                **{query: 0}).order_by('date_expiration')

            if promo:
                key = 'promo[0].%s' % service_type
                disc_rate = eval(key)
                whole, deci = divmod(balance, disc_rate)
                sec_avail = int(whole) * 60

        # If afforded/available seconds is greater than limit,
        # then we use the call duration limit
        if sec_avail > int(max_call_duration):
            ret = str(max_call_duration)
        # Else, use what's originally available
        else:
            ret = str(sec_avail)

        return Response(ret, status=status.HTTP_200_OK)


class QuotaDeduct(APIView):
    """ Applicable only for Bulk promo types
        Args:
            trans: transaction type, any of the ff combinations
                   ['U', 'B', 'D', 'G' ''] + ['local', 'outside']
                   + ['call', 'sms']
                   example: 'local_call', 'U_local_call'
            imsi: subscriber's IMSI
            amount: if sms transaction, default is 1
                    if call transaction, this is call duration (in mins)
            tariff: exisiting call_tariff, as returned by VBTS_Get_Call_Tariff
        Output:
            min_bal: minimum balance required
    """

    renderer_classes = (JSONRenderer,)

    def post(self, request, format=None):
        needed_fields = ["imsi", "trans", "amount"]
        if not all(i in request.POST for i in needed_fields):
            return Response("Missing Args", status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        promo_type, service_type = extract_types(request.data['trans'])
        amount = int(request.data['amount'])

        if promo_type == 'B':
            query = service_type + '__gte'
            subscription = PromoSubscription.objects.filter(
                contact__imsi__exact=imsi, promo__promo_type='B',
                **{query: amount}).order_by('date_expiration')

            if subscription:
                if 'local_sms' in service_type:
                    subscription[0].local_sms -= amount
                elif 'local_call' in service_type:
                    subscription[0].local_call -= amount
                elif 'globe_sms' in service_type:
                    subscription[0].globe_sms -= amount
                elif 'globe_call' in service_type:
                    subscription[0].globe_call -= amount
                elif 'outside_sms' in service_type:
                    subscription[0].outside_sms -= amount
                elif 'outside_call' in service_type:
                    subscription[0].outside_call -= amount
                subscription[0].save()

            ret = 'OK'
            status_code = status.HTTP_200_OK

        else:
            ret = 'Not Bulk promo'
            status_code = status.HTTP_400_BAD_REQUEST

        return Response(ret, status=status_code)


class GetPromoStatus(APIView):
    """
        <base_url>/api/promo/status?
        API call to query the status of a subscriber's promo subscription
    """
    renderer_classes = (JSONRenderer,)

    def post(self, request, format=None):
        needed_fields = ["imsi"]
        if not all(i in request.POST for i in needed_fields):
            return Response("Missing Args", status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        keyword = request.data['keyword']
        callerid = endaga_sub.get_numbers_from_imsi(imsi)[0]

        if not keyword:
            subscriptions = PromoSubscription.objects.filter(
                contact__imsi__exact=imsi). \
                order_by('date_expiration')
        else:
            subscriptions = PromoSubscription.objects.filter(
                contact__imsi__exact=imsi, promo__keyword=keyword). \
                order_by('date_expiration')
        if not subscriptions:
            send_sms.delay(callerid, '0000',
                           _("You have no %s subscriptions.") % keyword)

        else:
            msg = ""

            try:
                tz = Config.objects.get(key='timezone').value
            except Config.DoesNotExist:
                tz = pytz_timezone('Asia/Manila')

            for item in subscriptions:
                msg += "Your %s promo status: \\n" % item.promo.keyword
                expiry = item.date_expiration. \
                    astimezone(tz).strftime("%m/%d/%y %I:%M%p")

                if item.promo.promo_type == 'D' or item.promo.promo_type == 'G':
                    if item.local_sms:
                        msg += "%s local texts discount price: P%s\\n" % (
                            item.promo.keyword, mc_to_float(item.local_sms))
                    if item.local_call:
                        msg += "%s local call/min discount price: P%s\\n" % (
                            item.promo.keyword, mc_to_float(item.local_call))
                    if item.globe_sms:
                        msg += "%s Globe texts discount price: P%s\\n" % (
                            item.promo.keyword, mc_to_float(item.globe_sms))
                    if item.globe_call:
                        msg += "%s Globe call/min discount price: P%s\\n" % (
                            item.promo.keyword, mc_to_float(item.globe_call))
                    if item.outside_sms:
                        msg += "%s outside texts discount price: P%s\\n" % (
                            item.promo.keyword, mc_to_float(item.outside_sms))
                    if item.outside_call:
                        msg += "%s outside call/min discount price: P%s\\n" % (
                            item.promo.keyword, mc_to_float(item.outside_call))
                elif item.promo.promo_type == 'B':
                    if item.local_sms:
                        msg += "%s local texts: %s\\n" % (
                            item.promo.keyword, item.local_sms)
                    if item.local_call:
                        msg += "%s local call mins: %s\\n" % (
                            item.promo.keyword, item.local_call)
                    if item.globe_sms:
                        msg += "%s Globe texts: %s\\n" % (
                            item.promo.keyword, item.globe_sms)
                    if item.globe_call:
                        msg += "%s Globe call mins: %s\\n" % (
                            item.promo.keyword, item.globe_call)
                    if item.outside_sms:
                        msg += "%s outside texts: %s\\n" % (
                            item.promo.keyword, item.outside_sms)
                    if item.outside_call:
                        msg += "%s outside call mins: %s\\n" % (
                            item.promo.keyword, item.outside_call)
                elif item.promo.promo_type == 'U':
                    if item.local_sms:
                        msg += "%s unli local texts\\n" % item.promo.keyword
                    if item.local_call:
                        msg += "%s unli local calls\\n" % item.promo.keyword
                    if item.globe_sms:
                        msg += "%s unli Globe texts\\n" % item.promo.keyword
                    if item.globe_call:
                        msg += "%s unli Globe calls\\n" % item.promo.keyword
                    if item.outside_sms:
                        msg += "%s unli outside texts\\n" % item.promo.keyword
                    if item.outside_call:
                        msg += "%s unli outside calls\\n" % item.promo.keyword
                msg += "Exp: %s\\n" % expiry

            send_sms.delay(callerid, '0000', msg[:-2])

        return Response('OK', status=status.HTTP_200_OK)


class PromoUnsubscribe(APIView):
    renderer_classes = (JSONRenderer,)

    def post(self, request, format=None):
        needed_fields = ["imsi", "keyword"]
        if not all(i in request.POST for i in needed_fields):
            return Response("Missing Args", status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        keyword = request.data['keyword']
        callerid = endaga_sub.get_numbers_from_imsi(imsi)[0]
        subscriptions = PromoSubscription.objects.filter(
            contact__imsi__exact=imsi, promo__keyword=keyword)
        if not subscriptions:
            send_sms.delay(callerid, '0000',
                           _("You have no %s subscriptions.") % keyword)
            ret = 'FAIL UNSUBSCRIBE'
        else:
            for item in subscriptions:
                app.control.revoke(str(item.id), terminate=True)
            subscriptions.delete()
            msg = _("You are now unsubscribed from your %s promos.") % keyword
            send_sms.delay(callerid, '0000', msg)
            ret = 'OK UNSUBSCRIBE'

            # we should also create an event
            balance = endaga_sub.get_account_balance(imsi)
            reason = "Promo Cancel Subscription: %s" % keyword
            events.create_sms_event(imsi, balance,
                                    0, reason, '555')

        return Response(ret, status=status.HTTP_200_OK)


class GetPromoInfo(APIView):
    """
        <base_url>/api/promo/info?
        API call to get info on particular promo
    """
    renderer_classes = (JSONRenderer,)

    def post(self, request, format=None):
        needed_fields = ["keyword", "imsi"]
        if not all(i in request.POST for i in needed_fields):
            return Response("Missing Args", status=status.HTTP_400_BAD_REQUEST)

        imsi = request.data['imsi']
        keyword = request.data['keyword']
        callerid = endaga_sub.get_numbers_from_imsi(imsi)[0]

        try:
            promo = Promo.objects.get(keyword__exact=keyword)
            msg = promo.description
        except BaseException:
            msg = "You have entered an invalid promo keyword."
        send_sms.delay(callerid, '0000', msg)

        return Response('OK', status=status.HTTP_200_OK)
