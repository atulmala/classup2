from rest_framework import serializers

from .models import ParentCommunicationCategories, ParentCommunication


class ParentsCommunicationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentCommunicationCategories
        fields = ('category',)


class ParentCommunicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentCommunication
        fields = ('student', 'date_sent', 'category', 'communication_text',)
