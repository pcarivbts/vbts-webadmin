"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from locust import HttpLocust
from locust import TaskSet
from locust import task

base_url = 'http://127.0.0.1:7000'
test_servicekey = 'SAMPLE'
test_imsi = 'IMSI001010000000008'
test_imsi2 = 'IMSI001010000000009'


class ServiceSubscriptionBehavior(TaskSet):
    @task
    def service_status_normal(self):
        url = base_url + '/api/service/status'
        name = 'service_status_normal'
        data = {
            'imsi': test_imsi,
            'keyword': test_servicekey
        }
        self.client.post(url=url, data=data, name=name)

    @task
    def service_subscribe(self):
        """
            NOTE: give test_imsi2 a large amount of credit
            if we are going to do repetitive tests
        """
        data = {
            'imsi': test_imsi2,
            'keyword': test_servicekey
        }
        url = base_url + '/api/service/subscribe'
        with self.client.post(url=url, data=data,
                              catch_response=True) as response:
            if response.status_code == 500:
                print (response.text)

        url_ = base_url + '/api/service/unsubscribe'
        with self.client.post(url=url_, data=data,
                              catch_response=True) as response:
            if response.status_code == 400:
                print (response.text)


class ServiceQuotaUsageBehavior(TaskSet):
    @task
    def service_get_price(self):
        url = base_url + '/api/service/price'
        data = {
            'keyword': test_servicekey
        }
        self.client.post(url=url, data=data)

    @task
    def service_event(self):
        url = base_url + '/api/service/event'
        data = {
            'imsi': test_imsi,
            'keyword': test_servicekey
        }
        self.client.post(url=url, data=data)

        # NOTE: This will not work as service manager field
        # was removed in the service form
        # @task
        # def send_msg(self):
        #     url = base_url + '/api/service/send'
        #     data = {
        #         'imsi': 'IMSI0000000000',
        #         'keyword': test_servicekey,
        #         'msg': 'hello'
        #     }
        #     self.client.post(url=url, data=data)


class UserBehavior(TaskSet):
    tasks = {
        ServiceSubscriptionBehavior: 1,
        ServiceQuotaUsageBehavior: 1
    }


class WebsiteUser(HttpLocust):
    host = 'http://127.0.0.1:7000'
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 5000
