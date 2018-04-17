"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from dal import autocomplete
from vbts_webadmin.models import Circle, Contact
from vbts_subscribers.models import SipBuddies
from django.db.models import Q


class ContactAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return Contact.objects.none()

        qs = Contact.objects.all()
        if self.q:
            qs = qs.filter(Q(firstname__icontains=self.q) |
                           Q(lastname__icontains=self.q) |
                           Q(callerid__icontains=self.q))
        return qs


class CircleAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return Circle.objects.none()

        qs = Circle.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class SipBuddiesAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return SipBuddies.objects.none()

        qs = SipBuddies.objects.all()
        if self.q:
            qs = qs.filter(Q(firstname__icontains=self.q) |
                           Q(lastname__icontains=self.q) |
                           Q(callerid__icontains=self.q))
        return qs
