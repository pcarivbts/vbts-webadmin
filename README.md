# DEPRECATED
This project is no longer maintained. 

## About

The VBTS-Webadmin is a web-based management interface for the network operator
that allows him/her to manage services being run locally in the BTS.

## Setup
1. Setup `https://github.com/facebookincubator/CommunityCellularManager`
2. `cd` in to 'CommunityCellularManager/client' folder
3. Clone repo: `git submodule add https://github.com/pcarivbts/vbts-webadmin.git`
4. `cd` in to 'vbts-webadmin' folder.
5. Install requirements: `sudo pip install -r requirements.txt`
6. Install rabbitmq-server: `sudo apt-get install rabbitmq-server`
7. Run `python manage.py makemigrations`
8. Run `python manage.py migrate auth`
9. Run `python manage.py makemigrations vbts_webadmin`
10. Run `python manage.py migrate djcelery`
11. Run `python manage.py migrate --noinput`
12. Load our fixtures: `python manage.py loaddata vbts_webadmin/fixtures/config.json`
13. Create a superuser: `python manage.py createsuperuser`
14. Run the server: `python manage.py runserver <ip_address:port>`
15. Run Celery: `celery -A vbts_webadmin worker -l info --statedb=worker.state`

### You must also give the user 'vagrant' access to SR.
Workaround for Subscriber 'unable to open database error' for subscriber
registry table located in '/var/lib/asterisk/sqlite3dir/'

1. Add 'vagrant' user to 'www-data': `sudo usermod -a -G www-data vagrant`
2. Give group write access: `sudo chmod g+w /var/lib/asterisk/sqlite3dir/*`
3. Change group owner of the files:
   `sudo chown root:www-data /var/lib/asterisk/sqlite3dir/*`
4. Logout or reboot. That should do the trick.


## Testing

* To run the tests, you need to install the dependencies: `sudo pip install -r
requirements_dev.txt`.
* Run `python manage.py test` to run all the test cases.
* If there is a specific test suite that you want to run, then type `python
manage.py test vbts_webadmin.tests.{test_module}`

* To run locust tests
    * `cd` to the vbts_webadmin folder.
    * Run `locust -f vbts_webadmin/tests/locust/locustfile.py -n [num_of_requests]`
    * Open a web browser and access the locust interface at {machine_ip}:8089.
    For example, 127.0.0.1 if locust is ran locally.


## Deployment
1. Clone repo: `git clone https://github.com/pcarivbts/vbts-webadmin.git`
2. `cd` in to 'vbts-webadmin' folder.
3. Run 'fab [dev|lab] [options] deploy'. Options include:
* gsm stack: openbts or osmocom
* db: sqlite, postgre
* http_server: uwsgi_nginx, gunicorn_nginx, lighttpd

* Use 'dev' to deploy to VM and 'lab' to deploy to hardware

4. Restart the machine.
5. The WebAdmin can be accessed at {machine_ip}:7000.

## Roadmap
The goal is to refactor vbts-webadmin and integrate it with `https://github.com/facebookincubator/CommunityCellularManager`

## Others
Also read ['NOTES.md'](NOTES.md) for API description, programming notes,
and other details.
