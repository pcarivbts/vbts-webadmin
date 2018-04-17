"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.

Registers existing apps inside ../vbts-clientfiles/apps
into database

Usage:
    python manage.py reg_pcari_apps
"""

from __future__ import unicode_literals


import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from collections import OrderedDict

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError

from vbts_webadmin.models import Script


class NotRunningInTTYException(Exception):
    pass


class Command(BaseCommand):

    help = """

           Registers existing pcari-apps.
           Usage: python manage.py reg_pcari_apps <sudo_password>

           """
    CLIENTFILES_DIR = "/home/vagrant/client/vbts-clientfiles/packages"

    def install_setuppy(self, filepath, password):
        try:
            os.chdir(filepath)
            subprocess.Popen(
                'echo {} '
                ' | sudo python setup.py install --record installed_files.txt' .format(password),
                shell=False)
            return True
        except Exception as e:
            return False

    def is_package_installed(self, package):
        try:
            __import__(package)
            return True
        except ImportError:
            return False

    def save_to_db(self, details):
        sys.stdout.write(
            'Registering app: %(name)s | %(version)s ... \n' % details)
        script = Script(name=details['name'],
                        author=details['author'],
                        version=details['version'],
                        description=details['description'],
                        fs_script=details['fs_script'],
                        chatplan=details['chatplan'],
                        package_name="%s-%s" % (details['name'],
                                                details['version']),
                        )
        if 'arguments' in details:
            script.arguments = json.dumps(details['arguments'])
        script.save()

    def get_keypairs(self, text):
        dict = {}
        lines = text[6:-1].split('\n')
        for line in lines:
            line = line.strip()
            if "=" in line:
                pairs = line.split('=')
                key = pairs[0].strip("[]',")
                dict[key] = pairs[1].strip("[]',")
        return dict

    def parse_setup(self, text):
        start = text.find('setup(')
        text = text[start:]
        stack = 0
        for idx, char in enumerate(text[6:], 7):
            if char == ")":
                if stack:
                    stack -= 1
                else:
                    break
            elif char == "(":
                stack += 1

        return text[:idx]

    def get_script_details(self, filepath):

        filepath = os.path.join(settings.PCARI['DOWNLOADS_DIR'], filepath)
        script = {}

        # EXTRACT INFO from setup.py
        setuppy = os.path.join(filepath, 'setup.py')
        with open(setuppy) as f:
            script = self.get_keypairs(self.parse_setup(f.read()))

        # EXTRACT FS_SCRIPT
        fs_script_folder = os.path.join(filepath, 'fs_script')
        for f in os.listdir(fs_script_folder):
            if f.endswith(".py"):
                script['fs_script'] = f

        # EXTRACT JSON/XML FILES IF EXIST
        data_folder = os.path.join(filepath, 'data/')
        for f in os.listdir(data_folder):
            if f.endswith(".json"):
                with open(data_folder + f) as data:
                    script['arguments'] = json.load(
                        data, object_pairs_hook=OrderedDict)
            elif f.endswith(".xml"):
                script['chatplan'] = f
                shutil.copy(data_folder + f,
                            settings.PCARI['CHATPLAN_TEMPLATES_DIR'])

        return script

    def unzip_tar(self, path, file):
        try:
            filepath = os.path.join(path, file)
            tar = tarfile.open(filepath, "r:gz")
            tar.extractall(settings.PCARI['DOWNLOADS_DIR'])
            tar.close()
            index = re.search('.tar', file).start()
            tarfolder = file[:index]
            return os.path.join(settings.PCARI['DOWNLOADS_DIR'], tarfolder)
        except Exception as e:
            print (e)
            return None

    def install_pcari_scripts(self, password, dir=CLIENTFILES_DIR):
        sys.stdout.write('\n')
        for file in os.listdir(dir):
            tarfolder = self.unzip_tar(dir, file)
            sys.stdout.write('Installing package %s ... \n' % file)
            script = self.get_script_details(tarfolder)

            # USE fabfile to install plugins to avoid permission issue
            # is_installed = self.install_setuppy(tarfolder, password)
            is_imported = self.is_package_installed(script['name'])

            # Checks if package is installed and can be imported
            # if is_installed or is_imported:
            if is_imported:
                self.save_to_db(script)

    def execute(self, *args, **options):
        self.stdin = options.get('stdin', sys.stdin)
        return super(Command, self).execute(*args, **options)

    def handle(self, *args, **options):

        try:
            if hasattr(self.stdin, 'isatty') and not self.stdin.isatty():
                raise NotRunningInTTYException("Not running in a TTY")

            password = None

            while password is None:
                password = getpass.getpass()
                self.install_pcari_scripts(password)

        except KeyboardInterrupt:
            self.stderr.write("\nOperation cancelled.")
            sys.exit(1)

        except NotRunningInTTYException:
            self.stdout.write(
                "Scripts installation was skipped due to not running in a TTY. "
                "You can run `manage.py install_pcari_scripts` in your project "
                "to create install.")
