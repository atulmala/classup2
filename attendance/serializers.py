__author__ = 'atulgupta'

from rest_framework import serializers

from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ('student', 'date', 'the_class', 'section', 'subject')
