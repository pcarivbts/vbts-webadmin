"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _

from vbts_webadmin.forms import SearchForm
from vbts_webadmin.models import Group
from vbts_webadmin.models import ContactSimcards
from vbts_webadmin.models import ContactProfile


# class GroupForm(ModelForm):
#     def __init__(self, *args, **kwargs):
#         super(GroupForm, self).__init__(*args, **kwargs)
#         self.helper = FormHelper(self)
#         self.helper.layout.append(Submit('save', 'Save'))
#
#     class Meta:
#         model = Group
#         exclude = ['name']
#         widgets = {
#             'members': autocomplete.ModelSelect2Multiple(
#                 url='contact-autocomplete')
#         }


@login_required
def group_list(request, template_name='groups/list.html'):
    data = {}
    if 'search' in request.GET:
        groups = Group.objects.all()
        for term in request.GET['search'].split():
            # TODO: Improve this! Basically need reverse lookup
            # from contact to contactprofile
            groups = groups.filter(Q(name__icontains=term)
                                   | Q(owner__callerid__icontains=term))

        data['search'] = True
        alerts.info(request,
                    _("You've searched for: '%s'") % request.GET['search'])
    else:
        groups = Group.objects.all()
        # groups = ContactSimcards.objects.filter(contact__in=Group.objects.values_list('owner', flat=True))

    paginator = Paginator(groups, 15)

    page = request.GET.get('page')

    is_paginated = False
    if paginator.num_pages > 1:
        is_paginated = True

    try:
        groups = paginator.page(page)
    except PageNotAnInteger:
        groups = paginator.page(1)
    except EmptyPage:
        groups = paginator.page(paginator.num_pages)

    form = SearchForm(form_action='groups')
    data['groups'] = groups
    data['is_paginated'] = is_paginated
    data['form'] = form
    return render(request, template_name, data)


@login_required
def group_view(request, pk, template_name='groups/detail.html'):
    group = get_object_or_404(Group, pk=pk)
    # try:
    #     owner_profile = ContactProfile.objects.get(pk=group.owner)
    # except ContactProfile.DoesNotExist:
    #     owner_profile = None
    data = {
        'group': group,
        # 'owner_profile': owner_profile
    }
    return render(request, template_name, data)


@login_required
def group_delete(request, pk, template_name='groups/confirm_delete.html'):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.members.clear()
        group.delete()
        alerts.success(
            request,
            _("You've successfully deleted circle '%s.'") % group.name)
        return group_list(request)
    return render(request, template_name, {'group': group})
