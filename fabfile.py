"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.

Usage: fab dev|lab deploy
"""

from fabric.api import cd, local, env, get, lcd, put, run, require
from fabric.operations import sudo
import datetime

env.pkgfmt = "deb"
env.gsmeng = "osmocom"
env.depmap = {}
env.project_folder = 'vbts-webadmin'
env.project_name = 'vbts_webadmin'
env.media_folder = 'media'

"""Database credentials"""
env.db = 'postgre'
env.db_name = 'pcari'
env.db_user = 'pcari'
env.db_pass = 'pcari'

"""Superuser"""
env.user_name = 'pcari'
env.user_pass = 'pcari'
env.user_email = 'pcarivbts@gmail.com'


def dev():
    with lcd('../'):
        """ Host config for local Vagrant VM. """
        host = local('vagrant ssh-config %s | grep HostName' % (env.gsmeng,),
                     capture=True).split()[1]
        port = local('vagrant ssh-config %s | grep Port' % (env.gsmeng,),
                     capture=True).split()[1]
        env.hosts = ['vagrant@%s:%s' % (host, port)]
        identity_file = local('vagrant ssh-config %s | grep IdentityFile' %
                              (env.gsmeng,), capture=True)
        env.key_filename = identity_file.split()[1].strip('"')
        env.upload_path = 'pcari'
        env.path = '/var/www/%(project_name)s' % env


def lab():
    """ Host config for real hardware, lab version (i.e., default login). """
    env.hosts = ['endaga@192.168.1.25']
    env.password = 'endaga'
    env.path = '/var/www/%(project_name)s' % env
    env.upload_path = 'pcari'


def osmocom():
    """ Build Osmocom packages """
    env.gsmeng = "osmocom"


def lighttpd():
    """ Use lighttpd as the HTTP sever """
    env.http_server = 'lighttpd'


def postgre():
    """ Use postgre for Django database """
    env.db = 'postgre'


def gunicorn():
    """ Use gunicorn and nginx as HTTP server """
    env.http_server = 'gunicorn_nginx'


def deploy():
    """
    Deploy the latest version of the site to the servers,
    install any required third party modules,
    install the virtual host and then restart the webserver
    """
    require('hosts', provided_by=[dev, lab])
    require('path')
    # env.release = time.strftime('%Y%m%d%H%M%S')
    # For testing purposes, keep it 'current'
    env.release = 'current'
    setup()
    install_source()
    install_server()
    install_database()
    install_confs()
    restart_server()
    restart_supervisord()
    tune_server()


def setup():
    require('hosts', provided_by=[dev, lab])
    require('path')

    sudo('mkdir -p %(path)s' % env)
    sudo('chown -R www-data:www-data %(path)s/' % env)
    run('mkdir -p %(upload_path)s' % env)
    run('cd %(upload_path)s; mkdir -p releases; mkdir -p packages' % env)
    run('wget -P /tmp https://bootstrap.pypa.io/get-pip.py')
    sudo('python3 /tmp/get-pip.py')


def install_source():
    """Create an archive from the current Git master branch
    and upload it.
    """
    require('release', provided_by=[deploy, setup])
    with lcd('../%(project_folder)s' % env):
        # UNCOMMENT TO GIT ARCHIVE FROM MASTER
        # local('git archive --format=zip master > %(release)s.zip' % env )
        # local('git archive --format=zip plugins > %(release)s.zip' % env )
        local('tar -czvf %(release)s.tar.gz *' % env)
        local('ls -l')
        put('%(release)s.tar.gz' % env, '%(upload_path)s/packages/' % env)
        run('mkdir -p %(upload_path)s/releases/%(release)s' % env)
        run(
            'cd %(upload_path)s/releases/%(release)s && tar -xzvf ../../packages/%(release)s.tar.gz'
            % env, pty=False)
        local('rm %(release)s.tar.gz' % env)
        sudo('mkdir -p %(path)s' % env)
        sudo('cp -r %(upload_path)s/releases/%(release)s/* %(path)s/' % env)


def install_server():
    sudo('service lighttpd stop', pty=True)
    sudo('apt-get -y install nginx')
    sudo('apt-get -y install rabbitmq-server')

    sudo('pip install gunicorn')
    sudo('pip install envdir')

    require('release', provided_by=[deploy, setup])
    sudo('pip install -r %(upload_path)s/releases/%(release)s/requirements.txt'
         % env, pty=True)


def install_confs():
    require('release', provided_by=[deploy, setup])
    with cd('%(path)s' % env):
        # IGNORE FOR NOW
        # sudo('cp deploy/nginx/federer_nginx.conf '
        #      '/etc/nginx/sites-enabled/federer_nginx.conf'
        #       % env)

        media_folder = '%(path)s/%(project_name)s/%(media_folder)s/' % env
        sudo('chown -R www-data:www-data %s' % media_folder)

        sudo('if [ -a /etc/nginx/sites-enabled/default ]; '
             'then unlink /etc/nginx/sites-enabled/default; fi')

        sudo('cp deploy/nginx/nginx.conf '
             '/etc/nginx/nginx.conf')

        sudo('cp deploy/supervisor/webadmin-celeryd.conf '
             '/etc/supervisor/conf.d/webadmin-celeryd.conf')

        sudo('cp deploy/supervisor/webadmin-celerybeatd.conf '
             '/etc/supervisor/conf.d/webadmin-celerybeatd.conf')

        """ Install gunicornnginx configs and other needed files. """
        sudo('cp deploy/gunicorn/gunicorn_start.sh '
             '/bin/gunicorn_start.sh')

        sudo('chmod u+x /bin/gunicorn_start.sh')

        sudo('mkdir -p /etc/nginx/sites-enabled/')
        sudo('cp deploy/gunicorn/webadmin_nginx.conf '
             '/etc/nginx/sites-enabled/webadmin_nginx.conf')

        sudo('cp deploy/gunicorn/webadmin-gunicornd.conf '
             '/etc/supervisor/conf.d/webadmin-gunicornd.conf')


def install_database():
    """Create the database tables for all apps in INSTALLED_APPS
    whose tables have not already been created"""
    if env.db == 'postgre':
        run('sudo -u postgres psql -d template1 -c '
            '"CREATE DATABASE %s;" || true' % env.db_name)
        cmd = 'sudo -u postgres psql -d %(db_name)s -c ' \
              '"CREATE USER %(db_user)s WITH PASSWORD \'%(db_pass)s\'; ' \
              'GRANT ALL PRIVILEGES ON DATABASE %(db_name)s to %(db_user)s;" || true'
        sudo(cmd % env)
    require('path')
    with cd('%(path)s' % env):
        sudo('python3 manage.py makemigrations')
        sudo('python3 manage.py makemigrations vbts_webadmin')
        sudo('python3 manage.py migrate auth')
        sudo('python3 manage.py migrate djcelery')
        sudo('python3 manage.py migrate --noinput')
        sudo('python3 manage.py loaddata vbts_webadmin/fixtures/config.json')
        cmd = 'echo \"from django.contrib.auth.models import User; ' \
              'User.objects.create_superuser(' \
              '\'%(user_name)s\', \'%(user_email)s\', \'%(user_pass)s\')\" ' \
              '| python3 manage.py shell'
        sudo(cmd % env)
        sudo('echo \"yes\" | python3 manage.py collectstatic')
        sudo('cp -r static/ vbts_webadmin/')


def restart_server():
    """Restart nginx"""
    sudo('service nginx restart', pty=True)

    """Restart the lighttpd"""
    sudo('/etc/init.d/lighttpd restart', pty=True)


def restart_supervisord():
    """Reload supervisorctl conf to run celery and celerybeat"""
    sudo('supervisorctl reload', pty=True)


def tune_server():
    sudo('echo \'fs.file-max=500000\' >> /etc/sysctl.conf')
    # sudo('echo \'net.core.somaxconn=128\' >> /etc/sysctl.conf' % env)
    sudo('sysctl -p')
    sudo('echo \'www-data  soft  nofile  1024\' >> '
         '/etc/security/limits.conf')
    sudo('echo \'www-data  hard  nofile  4096\' >> '
         '/etc/security/limits.conf')


def clonedb():
    current_date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    require('path')
    with cd('%(path)s' % env):
        vbtswebadmin_db = 'backup_vbtswebadmindb_%s.json' % current_date
        sudo('python3 manage.py dumpdata vbts_webadmin     > %s' %
             vbtswebadmin_db)
        get(vbtswebadmin_db, vbtswebadmin_db)
        sudo('rm -f %s' % vbtswebadmin_db)
    hlr_db = 'backup_hlrdb_%s.db' % current_date
    hlr_path = '/var/lib/asterisk/sqlite3dir/sqlite3.db'
    get(hlr_path, hlr_db)
