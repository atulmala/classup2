from rest_framework import serializers
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import log_book


class LogBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = log_book
        fields = '__all__'

