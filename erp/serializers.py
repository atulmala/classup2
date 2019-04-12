__author__ = 'atulgupta'

from rest_framework import serializers

from .models import FeePaymentHistory


class FeeHistorySerialzer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    parent = serializers.StringRelatedField()

    class Meta:
        model = FeePaymentHistory
        fields = ('date', 'amount', 'fine', 'one_time', 'discount', 'mode', 'student', 'parent',
                  'cheque_number', 'bank', 'receipt_number')