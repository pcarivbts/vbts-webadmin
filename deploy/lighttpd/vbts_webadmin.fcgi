#Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
#The Village Base Station Project (PCARI-VBTS). All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree.

#!/usr/bin/python
import sys, os

# Add a custom Python path if were using virtualenv
#sys.path.insert(0, "/home/cere-ubuntu/pcari/vbts_webadmin/venv/lib")
#sys.path.insert(0, "/home/cere-ubuntu/pcari/vbts_webadmin/venv/lib/python2.7/")
#sys.path.insert(0, "/home/cere-ubuntu/pcari/vbts_webadmin/")
sys.path.insert(0, "/var/www/vbts_webadmin")


os.environ['DJANGO_SETTINGS_MODULE'] = "vbts_webadmin.settings.prod"

#runfastcgi(method="threaded", daemonize="false", maxspare=2)
#runfastcgi(method="prefork", daemonize="true", host="127.0.0.1", port="3033")
#runfastcgi(method="threaded", daemonize="false")

from django.core.servers.fastcgi import runfastcgi
runfastcgi(method="prefork", daemonize="true", host="127.0.0.1", port="7000")
