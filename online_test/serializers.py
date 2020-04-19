from rest_framework import serializers

from .models import OnlineTest, OnlineQuestion


class OnlineTestSerializer(serializers.ModelSerializer):
    the_class = serializers.StringRelatedField()
    subject = serializers.StringRelatedField()

    class Meta:
        model = OnlineTest


class OnlineQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineQuestion