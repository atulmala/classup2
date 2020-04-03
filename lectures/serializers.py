from rest_framework import serializers

from .models import Lecture


class LectureSerializer(serializers.ModelSerializer):
    teacher = serializers.StringRelatedField()
    the_class = serializers.StringRelatedField()
    subject = serializers.StringRelatedField()
    section = serializers.StringRelatedField

    class Meta:
        model = Lecture
