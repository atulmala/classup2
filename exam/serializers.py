from rest_framework import serializers

from .models import Wing


class WingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wing
        fields = ('school', 'wing', 'classes')
