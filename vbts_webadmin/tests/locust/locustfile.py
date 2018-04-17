"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from locust import HttpLocust
from locust import TaskSet
from locust import task


class UserBehavior(TaskSet):

    def on_start(self):
        """ Run on start for every Locust hatched """
        r = self.client.get('')
        self.client.post('',
                         {'username': 'pcari',
                          'email': '',
                          'password': 'pcari',
                          'csrfmiddlewaretoken': r.cookies['csrftoken']},
                         )

    @task(1)
    def dashboard(self):
        """ Access the dashboard """
        self.client.get("/dashboard")

    @task(1)
    def view_promo(self):
        self.client.get("/dashboard/promos")

    @task(1)
    def send_msg(self):
        response = self.client.get("/dashboard/message/send")
        csrftoken = response.cookies['csrftoken']
        data = {
            'recipients': 'IMSI001010000000008',
            'messgae': 'hello'
        }
        self.client.post("/dashboard/message/send", data=data,
                         headers={"X-CSRFToken": csrftoken})


class WebsiteUser(HttpLocust):
    host = 'http://192.168.1.25:7000'
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 5000
