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


class PromoSubscriptionBehavior(TaskSet):
    @task(1)
    def promo_status(self):
        url = base_url + '/api/promo/status'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()

    @task(1)
    def promo_subscribe(self):
        url = base_url + '/api/promo/subscribe'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()

    @task(1)
    def promo_unsubscribe(self):
        url = base_url + '/api/promo/unsubscribe'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()


class PromoQuotaUsageBehavior(TaskSet):
    @task(1)
    def promo_get_min_bal(self):
        url = base_url + '/api/promo/getminbal'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()

    @task(1)
    def promo_get_service_tariff(self):
        url = base_url + '/api/promo/getservicetariff'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()

    @task(1)
    def promo_get_service_type(self):
        url = base_url + '/api/promo/getservicetype'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()

    @task(1)
    def promo_get_seconds_available(self):
        url = base_url + '/api/promo/getsecavail'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()


class ServiceSubscriptionBehavior(TaskSet):
    @task(1)
    def status(self):
        url = base_url + '/api/service/status'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()

    @task(1)
    def subscribe(self):
        url = base_url + '/api/service/subscribe'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()

    @task(1)
    def unsubscribe(self):
        url = base_url + '/api/service/unsubscribe'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()


class ServiceAuxiliaryTasks(TaskSet):
    @task(1)
    def get_price(self):
        url = base_url + '/api/service/price'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()

    @task(1)
    def send_event(self):
        url = base_url + '/api/service/event'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()

    @task(1)
    def send_msg(self):
        url = base_url + '/api/service/send'
        with self.client.post(url=url, data={},
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()


class UserBehavior(TaskSet):
    tasks = {
        PromoSubscriptionBehavior: 1,
        PromoQuotaUsageBehavior: 10,
        ServiceAuxiliaryTasks: 10,
        ServiceSubscriptionBehavior: 1
    }

    @task
    def index(self):
        pass


class WebsiteUser(HttpLocust):
    host = 'http://127.0.0.1:7000'
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 5000
