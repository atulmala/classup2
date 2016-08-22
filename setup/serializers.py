from rest_framework import serializers

from .models import Configurations


class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configurations
        fields = ('enable_bus_attendance', )
