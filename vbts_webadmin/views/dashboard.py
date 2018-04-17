"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import pytz
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout, Submit
from django.conf import settings
from django.contrib import messages as alerts
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.urlresolvers import reverse_lazy
from django.forms import CharField
from django.forms import ChoiceField
from django.forms import EmailField
from django.forms import Form
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import ugettext as _

from vbts_webadmin.models import UserProfile


class UpdateProfileForm(Form):
    email = EmailField(required=False, label=_("Email"))
    first_name = CharField(required=False, label=_("First name"))
    last_name = CharField(required=False, label=_("Last name"))
    lang = ChoiceField(required=True, label=_("Language"),
                       choices=settings.LANGUAGES)
    tz = ChoiceField(required=True, label=_("Timezone"),
                     choices=[(x, x) for x in pytz.common_timezones])

    def __init__(self, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-updateProfileForm'
        self.helper.form_method = 'post'
        self.helper.form_action = '/dashboard/profile/update'
        self.helper.form_class = 'profile-form'
        self.helper.layout = Layout(
            'email', 'first_name', 'last_name', 'lang', 'tz')
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('profile', kwargs={}),
                'Cancel')
        ))


class ChangePasswordForm(PasswordChangeForm):
    """Change password form visible on user profile page."""

    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-updateAccountForm'
        self.helper.form_method = 'post'
        self.helper.form_action = '/dashboard/profile/password/change'
        self.helper.form_class = 'profile-form'
        self.helper.layout = Layout(
            'old_password', 'new_password1', 'new_password2', )
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML(
            '<a href="{}" class="btn btn-default" role="button">{}</a>'.format(
                reverse_lazy('profile', kwargs={}),
                'Cancel')
        ))


@login_required
def home(request):
    return render(request, "dashboard.html",
                  {'username': request.user.username})


@login_required
def profile_change_password(
        request,
        template_name='accounts/password_form.html'):
    """Handles password change request data."""

    if request.method == 'POST':
        password_form = ChangePasswordForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Important!
            alerts.success(request, _(
                'Your password was successfully updated!'))
            return redirect('profile')
    else:
        password_form = ChangePasswordForm(request.user)

    return render(request, template_name, {'password_form': password_form, })


@login_required
def profile_update(request, template_name='accounts/profile_form.html'):
    user_profile = UserProfile.objects.get(user=request.user)
    profile_form = UpdateProfileForm({
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'lang': user_profile.language,
        'tz': user_profile.timezone
    })
    context = {
        'user_profile': user_profile,
        'profile_form': profile_form,
    }
    if request.POST and profile_form.is_valid():
        if 'email' in request.POST:
            request.user.email = request.POST['email']
        if 'first_name' in request.POST:
            request.user.first_name = request.POST['first_name']
        if 'last_name' in request.POST:
            request.user.last_name = request.POST['last_name']
        user_profile = UserProfile.objects.get(user=request.user)
        if 'lang' in request.POST:
            user_profile.language = request.POST['lang']
        if 'tz' in request.POST:
            user_profile.timezone = request.POST['tz']
        user_profile.save()
        request.user.save()
        alerts.success(request, _("You've successfully updated your profile."))
        return redirect('profile')
    return render(request, template_name, context)


@login_required
def profile_view(request, template_name='accounts/detail.html'):
    user_profile = UserProfile.objects.get(user=request.user)
    return render(request, template_name,
                  {'user': request.user, 'user_profile': user_profile})
