from rest_framework import serializers

from .models import *


class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        exclude = ()


class TimeTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeTable
        exclude = ()

class TeacherWingMappingSerializer (serializers.ModelSerializer):
    class Meta:
        model = TeacherWingMapping
        exclude = ()

class ArrangementSerializer (serializers.ModelSerializer):
    school = serializers.SlugRelatedField (read_only=True, slug_field='school_name')
    the_class = serializers.SlugRelatedField (read_only=True, slug_field='standard')
    section = serializers.SlugRelatedField (read_only=True, slug_field='section')
    period = serializers.SlugRelatedField (read_only=True, slug_field='period')

    class Meta:
        model = Arrangements
        exclude = ()


class CTimeTableSerializer(serializers.ModelSerializer):
    the_class = serializers.SlugRelatedField(read_only=True, slug_field='standard')
    section = serializers.SlugRelatedField(read_only=True, slug_field='section')
    subject = serializers.SlugRelatedField(read_only=True, slug_field='subject_name')
    period = serializers.SlugRelatedField(read_only=True, slug_field='period')

    class Meta:
        model = CTimeTable
        exclude = ()
