"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from core import number_utilities
from django.utils import timezone as timezone
from django.utils.translation import ugettext as _
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from vbts_webadmin.models import Config
from vbts_webadmin.models import Contact
from vbts_webadmin.models import Group
from vbts_webadmin.models import GroupMembers
from vbts_webadmin.models import Message
from vbts_webadmin.models import MessageRecipients
from vbts_webadmin.tasks import send_sms


def add_group_members(mems, group):
    """
        Adds group member entries
    Args:
        mems: CSV of member callerIDs
        group: Group instance in which callerIDs will be added

    Returns:
        invalid: list containing caller ids that the system failed to add
                 if all numbers were successfully added, this is an empty list
    """

    invalid = []
    for caller_id in str(mems).split(','):
        if not caller_id:
            continue
        try:
            caller_id = number_utilities.canonicalize(caller_id)

            if len(caller_id) < 10 or len(caller_id) > 12:
                raise Exception("Canonicalized cellphone numbers "
                                "must be 12 digits long and "
                                "canonicalized landline numbers "
                                "must be 10 digits long.")

            # Also handle caller_ids that are not within VBTS network
            try:
                mem = Contact.objects.get(callerid=caller_id)
            except BaseException:
                mem = Contact.objects.create(imsi="OFFNET" + caller_id,
                                             callerid=caller_id)

            GroupMembers.objects.create(user=mem,
                                        group=group)
        except BaseException:
            invalid.append(caller_id)

    return invalid


class CreateGroup(APIView):
    """ Create a group; to be used in F&F promo
        <base_url>/api/group?
        Data arguments:
            name:   name of the circle
            mems:   CSV of member callerids
            imsi:   IMSI of circle creator
    """

    renderer_classes = (JSONRenderer,)

    def post(self, request):
        """ POST method for creating a group """

        needed_fields = ["imsi", "name", "mems"]
        if not all(i in request.POST for i in needed_fields):
            return Response('ERROR', status=status.HTTP_400_BAD_REQUEST)

        requester = Contact.objects.get(imsi=request.data['imsi'])

        # We put code to optionally the number of groups that a user can
        # create. This depends on the max number declared in the configs

        max_groups_per_subscriber = Config.objects.get(
            key='max_groups_per_subscriber').value
        count = Group.objects.filter(owner=requester).count()
        if max_groups_per_subscriber == 'NA':
            pass  # unlimited, do nothing
        elif count >= int(max_groups_per_subscriber):
            send_sms.delay(requester.callerid, '0000',
                           _("You have too many groups and have exceeded the"
                             " allowed limits."))
            return Response("Too many groups",
                            status=status.HTTP_403_FORBIDDEN)

        # TODO: Validate when empty members are passed
        # members are passed in this format: 'Num1,Num2,Num3,Num4,Num5'
        if not request.data['mems']:
            send_sms.delay(requester.callerid, '0000',
                           _("You did not input any member contact numbers."))
            return Response("Empty Mem Fields",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            new_group = Group()
            new_group.owner = requester
            # To all caps or not to all caps?
            new_group.name = request.data['name'].upper()
            new_group.save()
        except BaseException:
            # unique_together constaint failed, among other things
            send_sms.delay(requester.callerid, '0000',
                           "Failed to create group %s."
                           % request.data['name'])
            return Response('Constraint Failed',
                            status=status.HTTP_400_BAD_REQUEST)

        mems = request.data['mems']
        invalid = add_group_members(mems, new_group)

        send_sms.delay(new_group.owner.callerid, '0000',
                       _("Your group %s has been successfully created.")
                       % new_group.name)
        if invalid:
            send_sms.delay(new_group.owner.callerid, '0000',
                           _("Failed to add the following to group "
                             "%(group)s. %(invalid)s") % ({
                                 'group': new_group.name,
                                 'invalid': str(invalid)
                             }))
        return Response('OK CREATED', status=status.HTTP_200_OK)


class EditGroupMems(APIView):
    """ Edit members of the group
        <base_url>/api/group/edit
        Data arguments:
            name:   name of the circle
            mems:   CSV of member callerids
            imsi:   IMSI of circle creator
    """

    renderer_classes = (JSONRenderer,)

    def post(self, request):
        """ POST method for creating a group """

        needed_fields = ["imsi", "name", "mems"]
        if not all(i in request.POST for i in needed_fields):
            return Response('ERROR', status=status.HTTP_400_BAD_REQUEST)

        requester = Contact.objects.get(imsi=request.data['imsi'])
        mems = request.data['mems']

        # TODO: Validate when empty members are passed
        # members are passed in this format: 'Num1,Num2,Num3,Num4,Num5'
        if not request.data['mems']:
            send_sms.delay(requester.callerid, '0000',
                           "You did not input any member contact numbers.")
            return Response("Empty Mem Fields",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            group = Group.objects.get(name__exact=request.data['name'],
                                      owner__imsi=request.data['imsi'])
        except BaseException:
            send_sms.delay(requester.callerid, '0000',
                           _("Requested group %s does not exist.") %
                           request.data['name'])
            return Response('ACCESS GROUP FAIL',
                            status=status.HTTP_400_BAD_REQUEST)

        delta = timezone.now() - group.last_modified

        try:
            group_edit_interval = Config.objects.get(
                key='group_edit_interval').value
        except Config.DoesNotExist:
            group_edit_interval = 30

        if delta.days < group_edit_interval:
            send_sms.delay(
                requester.callerid, '0000',
                _("You can only edit the group %s once in every %s days.") %
                (request.data['name'], group_edit_interval))
            return Response('GROUP EDIT LIMIT EXCEEDED',
                            status=status.HTTP_400_BAD_REQUEST)

        else:
            group.members.clear()   # clear existing group members first
            group.save()            # then add the new set of members
            invalid = add_group_members(mems, group)

        send_sms.delay(group.owner.callerid, '0000',
                       _("Your group %s has been successfully edited.")
                       % group.name)
        if invalid:
            send_sms.delay(group.owner.callerid, '0000',
                           _("However, we failed to add the following to "
                             "group %(group)s. %(invalid)s") % ({
                                 'group': group.name,
                                 'inavlid': str(invalid)
                             }))
        return Response('OK EDIT', status=status.HTTP_200_OK)


class DeleteGroup(APIView):
    """ Delete a group
        <base_url>/api/group/delete
        Data arguments:
            imsi: IMSI of the author
            name: name of the group
    """

    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request, format=None):
        """ POST method for deleting a group """

        if not ("name" in request.POST or "imsi" in request.POST):
            return Response("ERROR", status=status.HTTP_400_BAD_REQUEST)

        requester = Contact.objects.get(imsi=request.data['imsi'])

        try:
            group = Group.objects.get(name__exact=request.data['name'],
                                      owner__imsi=request.data['imsi'])
            group.members.clear()
            group.delete()
            send_sms.delay(requester.callerid, '0000',
                           _("Successfully deleted group %s.")
                           % request.data['name'])
            return Response('DELETE OK', status=status.HTTP_200_OK)
        except BaseException:
            send_sms.delay(requester.callerid, '0000',
                           _("Failed to delete group %s.")
                           % request.data['name'])
            return Response('DELETE FAIL', status=status.HTTP_400_BAD_REQUEST)


class SendGroupMsg(APIView):
    """ Send a message to a group
        <base_url>/api/group/send?
        Data arguments:
            gname:  groupname of the target recipient
            imsi:   IMSI of message sender
            msg:    the message to be sent
    """

    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request, format=None):
        """ POST method to send a message to a circle or UE """

        needed_fields = ["imsi", "name", "msg"]
        if not all(i in request.POST for i in needed_fields):
            return Response("", status=status.HTTP_400_BAD_REQUEST)

        try:
            sender = Contact.objects.get(imsi=request.data['imsi'])
            group = Group.objects.get(name=request.data['name'])
            members = GroupMembers.objects.filter(group_id=group.id)
        except BaseException:
            return Response("Args failed", status=status.HTTP_400_BAD_REQUEST)

        # Check that sender is part of the group nor owner
        if not members.filter(user=sender) \
                and group.owner.imsi != request.data['imsi']:
            send_sms.delay(sender.callerid, '0000',
                           _("FORBIDDEN. You are not a member of this group."))
            return Response("Forbidden", status=status.HTTP_403_FORBIDDEN)

        message = Message.objects.create(author=sender,
                                         message=request.data['msg'])
        message.published_date = timezone.now()
        message.save()

        failed = []
        invalid_callerid = False

        for member in members:
            recipient = MessageRecipients.objects.create(message=message,
                                                         user=member.user)
            try:
                send_sms.delay(recipient.user.callerid,
                               sender.callerid,
                               message.message)
                recipient.save()

            except openbts.exceptions.InvalidRequestError:
                invalid_callerid = True
                failed.append(recipient.user.callerid)

        if invalid_callerid:
            send_sms.delay(sender.callerid, '0000',
                           _("Failed to send your message to: %s.") % failed)
            return Response("", status=status.HTTP_400_BAD_REQUEST)
        else:
            send_sms.delay(sender.callerid, '0000',
                           _("Successfully sent your message to the group."))
            return Response('OK SEND', status=status.HTTP_200_OK)
