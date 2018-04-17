"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from datetime import datetime

from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from vbts_webadmin.models import Service


class JSONSerializerField(serializers.Field):
    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class ServiceSerializer(serializers.ModelSerializer):
    script_arguments = JSONSerializerField()

    class Meta:
        model = Service
        fields = ('name', 'keyword', 'number', 'script', 'script_arguments')


@api_view(['GET'])
def service_details(request):
    """
    Get service details
    """
    try:
        task = Service.objects.get(keyword__exact=request.GET['keyword'])
    except Service.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ServiceSerializer(task)
        return Response(serializer.data)
