from  rest_framework import serializers

from .models import SMSRecord


class SMSDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSRecord
        fields = ('id', 'date', 'message', 'sender_type')
