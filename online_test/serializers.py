from rest_framework import serializers

from .models import OnlineTest, OnlineQuestion


class OnlineTestSerializer(serializers.ModelSerializer):
    the_class = serializers.StringRelatedField()
    subject = serializers.StringRelatedField()
    teacher = serializers.StringRelatedField()
    exam = serializers.StringRelatedField()

    class Meta:
        model = OnlineTest
        exclude = ()


class OnlineQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineQuestion
        exclude = ()
