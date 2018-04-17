"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import json
import os
import re
import shutil
import subprocess
import tarfile
import urllib

import requests
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.conf import settings
from django.contrib import messages as alerts
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import ugettext as _

from vbts_webadmin.models import Script


class SearchForm(forms.Form):
    search = forms.CharField(max_length=800, required=False)
    where_choices = (
        ('0', 'My Plugins'),
        ('1', 'Available Plugins'),
    )
    where_to_search = forms.ChoiceField(
        required=False,
        choices=where_choices,
        widget=forms.RadioSelect(attrs={'class': 'where_to_search'}))

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_id = 'search-plugins-form'
        self.helper.form_class = 'form-inline'
        self.helper.action = reverse_lazy('plugins')
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            'where_to_search',
            'search',
        )
        self.helper.add_input(Submit('', 'Search', css_class='btn-primary'))


@login_required
def plugin_list(request, template_name='plugins/list.html'):
    data = {}
    params = {}
    if 'search' in request.POST:
        params['search'] = request.POST['search']
    all_plugins = requests.get(settings.PCARI['CLOUD_URL']
                               + "pcari-plugins", params=params)
    plugins = json.loads(all_plugins.text)
    data['scripts'] = [str(item) for item in
                       Script.objects.all().values_list('id', flat=True)]
    data['plugins'] = plugins
    form = SearchForm({'where_to_search': '1'})
    data['form'] = form
    return render(request, template_name, data)


def plugin_download(download_url, filepath):
    # TODO: Replace HTTP with FTP and credentials | SETUP FTP
    # FTP with credentials
    # urllib.urlretrieve('ftp://username:password@server/path/to/file', 'filepath')
    urllib.urlretrieve(download_url, filepath)
    # Unzip downloaded file
    tar = tarfile.open(filepath, "r:gz")
    tar.extractall(settings.PCARI['DOWNLOADS_DIR'])
    tar.close()
    # Returns path of extracted folder
    index = re.search('.tar', filepath).start()
    tarfolder = filepath[:index]
    return tarfolder


@login_required
def plugin_install(request, pk, template_name='plugins/confirm_install.html'):
    params = {'id': pk}
    plugins = requests.get(settings.PCARI['CLOUD_URL'] + "pcari-plugins",
                           params=params)
    plugin = json.loads(plugins.text)
    if request.method == 'POST' and request.POST['password']:

        try:
            download_url = settings.PCARI['PLUGINS_DOWNLOAD_URL'] + \
                plugin['id']
            filepath = os.path.join(settings.PCARI['DOWNLOADS_DIR'],
                                    plugin['package'])
            chatplan = ""
            fs_script = ""
            script_args = {}
            plugin_folder = plugin_download(download_url, filepath)
            fsscript_folder = plugin_folder + "/fs_script/"
            for f in os.listdir(fsscript_folder):
                if f.endswith(".py"):
                    fs_script = f

            data_folder = plugin_folder + '/data/'
            for f in os.listdir(data_folder):
                if f.endswith(".json"):
                    with open(data_folder + f) as data:
                        script_args = json.load(data)
                elif f.endswith(".xml"):
                    chatplan = f
                    shutil.copy(data_folder + f,
                                settings.PCARI['CHATPLAN_TEMPLATES_DIR'])

            script, created = Script.objects.get_or_create(id=plugin['id'])
            script.name = plugin['name']
            script.version = plugin['version']
            script.author = plugin['author']
            script.description = plugin['description']
            script.package_name = plugin['package']
            script.status = 'D'
            script.fs_script = fs_script
            script.arguments = script_args
            script.chatplan = chatplan
            script.save()

            # INSTALL setup.py
            os.chdir(plugin_folder)
            password = request.POST['password']
            # TODO: integrate pwd in subprocess
            subprocess.Popen(
                'echo {} | sudo python setup.py install --record installed_files.txt' .split(),
                shell=False)

            os.remove(filepath)
        except Exception as e:
            print (e)
            return redirect(reverse_lazy('plugins'))

        alerts.success(request,
                       _("You've successfully installed the plugin '%s.'")
                       % script)
        return redirect(reverse_lazy('plugins'))

    return render(request, template_name, {'script': plugin})


@login_required
def plugin_uninstall(request, pk,
                     template_name='plugins/confirm_uninstall.html'):
    script = get_object_or_404(Script, id=pk)
    if request.method == 'POST' and request.POST['password']:

        filename = "%s-%s" % (script.name, script.version)
        plugin_folder = os.path.join(settings.PCARI['DOWNLOADS_DIR'],
                                     filename)
        try:
            os.chdir(plugin_folder)
            # TODO: integrate pwd in subprocess
            password = request.POST['password']
            subprocess.Popen(
                'echo {} | sudo cat installed_files.txt | sudo xargs rm -rf'
                .split(), shell=False)
            shutil.rmtree(plugin_folder)
        except OSError:
            pass

        script.delete()
        alerts.success(request,
                       _("You've successfully uninstalled the plugin '%s.'")
                       % script.name)
        return redirect(reverse_lazy('plugins'))
    return render(request, template_name, {'script': script})


@login_required
def plugin_view(request, pk, template_name='plugins/detail.html'):
    script = get_object_or_404(Script, pk=pk)
    return render(request, template_name, {'script': script, 'pk': pk})
