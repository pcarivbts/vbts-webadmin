"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse_lazy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.layout import Div
from crispy_forms.layout import ButtonHolder
from crispy_forms.layout import Submit
from crispy_forms.bootstrap import AppendedText
from crispy_forms.bootstrap import PrependedText
from crispy_forms.bootstrap import FormActions


class LoginForm(AuthenticationForm):

    """ Form to input user credentials """

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            FormActions(
                Submit('login', 'Login', css_class="btn-primary")
            )
        )


class SearchForm(forms.Form):
    search = forms.CharField(max_length=500)

    def __init__(self, *args, **kwargs):
        self.form_action = kwargs.pop('form_action')
        super(SearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.form_class = 'form-inline'
        self.helper.form_show_labels = False
        self.helper.form_action = reverse_lazy(self.form_action)
        self.helper.add_input(Submit('', 'Search', css_class='btn-primary'))
