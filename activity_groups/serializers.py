from rest_framework import serializers

from .models import *


class ActivityGroupSerializer (serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(ActivityGroupSerializer, self).__init__(many=many, *args, **kwargs)

    group_incharge = serializers.StringRelatedField(many=False)
    incharge_email = serializers.SerializerMethodField()

    class Meta:
        model = ActivityGroup
        fields = ('id', 'school', 'group_name', 'group_incharge', 'incharge_email')

    def get_incharge_email(self, obj):
        return obj.group_incharge.email


class ActivityGroupMembersSerializer (serializers.ModelSerializer):
    student = serializers.StringRelatedField(many=False)

    class Meta:
        model = ActivityMembers
