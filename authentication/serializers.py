from rest_framework import serializers

from .models import log_book


class LogBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = log_book

