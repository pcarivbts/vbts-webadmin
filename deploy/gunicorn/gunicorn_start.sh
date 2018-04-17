#!/bin/bash
#Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
#The Village Base Station Project (PCARI-VBTS). All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree.

NAME="vbts_webadmin"                                # Name of the application
DJANGODIR=/var/www/vbts_webadmin                    # Django project directory
SOCKFILE=/var/www/vbts_webadmin/vbts_webadmin.sock  # we will communicte using this unix socket
USER=www-data                                       # the user to run as
GROUP=www-data                                      # the group to run as
NUM_WORKERS=3        # how many worker processes should Gunicorn spawn, Usually  2* CPU + 1
DJANGO_WSGI_MODULE=vbts_webadmin.wsgi               # WSGI module name
TIMEOUT=60

echo "Starting $NAME as `whoami`"

cd $DJANGODIR
# Activate the virtual environment
# source ../bin/activate
# export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
# export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=- \
  --timeout=$TIMEOUT
