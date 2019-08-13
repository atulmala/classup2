from rest_framework import serializers

from .models import ImageVideo


class ImageVideoSerializer(serializers.ModelSerializer):
    the_class = serializers.StringRelatedField()
    section = serializers.StringRelatedField()

    class Meta:
        model = ImageVideo
        fields = ('id', 'type', 'teacher', 'the_class', 'section', 'creation_date', 'descrition', 'location',)