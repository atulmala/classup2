from rest_framework import serializers

from .models import *


class TimeTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeTable
