__author__ = 'atulgupta'

from rest_framework import serializers

from academics.models import TeacherSubjects, Teacher
from .models import TeacherAttendance, TeacherAttendnceTaken


class TeacherSubjectSerializer(serializers.ModelSerializer):
    subject = serializers.StringRelatedField()
    teacher = serializers.StringRelatedField()

    class Meta:
        model = TeacherSubjects
        fields = ('teacher', 'subject',)


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ('id', 'first_name', 'last_name', 'email', 'mobile', 'active_status')


class TeacherAttendanceSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(TeacherAttendanceSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = TeacherAttendance
        fields = ('id', 'school', 'date', 'teacher',)

