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
test_promokey = 'SDISC'
test_imsi = 'IMSI001010000000008'
test_imsi2 = 'IMSI001010000000009'


class PromoSubscriptionBehavior(TaskSet):
    @task(1)
    def promo_status_normal(self):
        url = base_url + '/api/promo/status'
        name = 'promo_status_normal'
        data = {'imsi': test_imsi, 'keyword': test_promokey}
        self.client.post(url=url, data=data, name=name)

    @task(1)
    def promo_subscribe(self):
        """
            NOTE: give test_imsi2 a large amount of credit
            if we are going to do repetitive tests
        """
        data = {'imsi': test_imsi2, 'keyword': test_promokey}
        url = base_url + '/api/promo/subscribe'
        self.client.post(url=url, data=data)

        url = base_url + '/api/promo/unsubscribe'
        self.client.post(url=url, data=data)


class PromoQuotaUsageBehavior(TaskSet):
    @task(1)
    def promo_get_min_bal(self):
        url = base_url + '/api/promo/getminbal'
        data = {
            'trans': 'U_local_sms',
            'tariff': 100000
        }
        self.client.post(url=url, data=data)

    @task(1)
    def promo_get_service_tariff(self):
        url = base_url + '/api/promo/getservicetariff'
        data = {
            'imsi': test_imsi,
            'trans': 'U_local_sms',
            'dest': ''
        }
        self.client.post(url=url, data=data)

    @task(1)
    def promo_get_service_type(self):
        url = base_url + '/api/promo/getservicetype'
        data = {
            'imsi': test_imsi,
            'trans': 'local_sms',
            'dest': '631234567'
        }
        self.client.post(url=url, data=data)

    @task(1)
    def promo_get_seconds_available(self):
        url = base_url + '/api/promo/getsecavail'
        data = {
            'imsi': test_imsi,
            'trans': 'U_local_sms',
            'balance': 1000000,
            'dest': '6312345678'
        }
        self.client.post(url=url, data=data)

    @task
    def promo_quota_deduct(self):
        url = base_url + '/api/promo/deduct'
        data = {
            'imsi': test_imsi,
            'trans': 'U_local_sms',
            'amount': 100000,
            'dest': '6312345678'
        }
        # applicable only for bulk type
        with self.client.post(url=url, data=data,
                              catch_response=True) as response:
            if response.status_code == 400:
                response.success()


class UserBehavior(TaskSet):
    tasks = {
        PromoSubscriptionBehavior: 1,
        PromoQuotaUsageBehavior: 1
    }


class WebsiteUser(HttpLocust):
    host = 'http://127.0.0.1:7000'
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 5000
