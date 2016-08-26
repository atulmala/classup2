__author__ = 'atulgupta'

from rest_framework import serializers

from academics.models import TeacherSubjects


class TeacherSubjectSerializer(serializers.ModelSerializer):

    subject = serializers.StringRelatedField()
    teacher = serializers.StringRelatedField()

    class Meta:
        model = TeacherSubjects
        fields = ('teacher', 'subject',)

