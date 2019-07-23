from rest_framework import serializers

from .models import ImageVideo


class ImageVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageVideo
        fields = ('teacher', 'the_class', 'section', 'creation_date', 'descrition', 'location',)