"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.

-
Utility functions for VBTS-WebAdmin
"""

import math

from django.utils import timezone
from djcelery.models import IntervalSchedule
from djcelery.models import PeriodicTask


def float_to_mc(value):
    """
    Convert from float to millicents
    Args:
        value: float number
    Returns: value in millcents

    """
    return int(value * 100 * 1000)


def mc_to_float(value):
    """
    Convert from millicents to float
    Args:
        value: millicent number
    Returns: value in float

    """
    return float(value) / (100 * 1000)


def msg_chop(long_msg):
    """
        Chops the message into 150-char blocks and prepends (XX/YY)
    Args:
        long_msg: the original, long message string

    Returns:
        msg_blocks: list where each element is a 150-char msg block
    """
    if len(long_msg) < 160:
        return [long_msg]  # it fits, nothing to do here
    else:
        block_size = 150  # allot 10 chars for prepended (XX/YY)
        block_num = int(math.ceil(len(long_msg) / float(block_size)))
        msg_blocks = []

        for i in range(0, block_num):
            start = i * block_size
            msg_blocks.append("(%s/%s) %s" % (
                i + 1, block_num, long_msg[start:start + block_size]))
        return msg_blocks


def clean_string(string):
    """
        Remove unicode characters and escape newline chars
        To be used for string output from twitter/rss apps
    Args:
        string: text to be cleaned

    Returns:

    """
    return string.encode('ascii', 'ignore').replace('\n', '\\n')


def manage_interval(period, every):
    """ adapted from
        https://groups.google.com/forum/#!msg/celery-users/CZXCh8sCK5Q/ihZgMV2HWWYJ
        c/o Jean Mark
    """
    permissible_periods = ['days', 'hours', 'minutes', 'seconds']
    if period not in permissible_periods:
        raise Exception('Invalid period specified')

    # query intervals
    interval_schedules = IntervalSchedule.objects.filter(period=period,
                                                         every=every)

    # just check if interval schedules exist like that already and reuse em
    if interval_schedules:
        interval_schedule = interval_schedules[0]
    # else, create a brand new interval schedule
    else:
        interval_schedule = IntervalSchedule()
        interval_schedule.every = abs(every)
        interval_schedule.period = period
        interval_schedule.save()

    return interval_schedule


def create_periodic_task(task_name, period, every, args=None, kwargs=None):
    """ adapted from
        https://groups.google.com/forum/#!msg/celery-users/CZXCh8sCK5Q/ihZgMV2HWWYJ
        c/o Jean Mark

        Schedules a task by name every "every" "period".
        So an example call would be:
            create_periodic_task('mycustomtask', 'seconds', 30, [1,2,3])
        that would schedule your custom task to run every 30 seconds
        with the arguments 1,2 and 3 passed to the actual task.
    """
    # create the schedule
    interval_schedule = manage_interval(period, every)
    # create the periodic task
    ptask_name = "%s_%s" % (task_name, timezone.now())
    ptask = PeriodicTask(name=ptask_name, task=task_name,
                         interval=interval_schedule)
    if args:
        ptask.args = args
    if kwargs:
        ptask.kwargs = kwargs
    ptask.save()
    return ptask
