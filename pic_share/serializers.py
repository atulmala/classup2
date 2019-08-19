import json

from rest_framework import serializers

from .models import ImageVideo, ShareWithStudents


class ImageVideoSerializer(serializers.ModelSerializer):
    the_class = serializers.StringRelatedField()
    section = serializers.StringRelatedField()

    class Meta:
        model = ImageVideo
        fields = ('id', 'type', 'teacher', 'the_class', 'section', 'creation_date',
                  'descrition', 'location', 'short_link',)


class SharedWithSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    teacher = serializers.SerializerMethodField()
    the_class = serializers.StringRelatedField()
    section = serializers.StringRelatedField()
    creation_date = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    descrition = serializers.SerializerMethodField()
    short_link = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = ShareWithStudents
        fields = ('id', 'type', 'teacher', 'the_class', 'section', 'creation_date', 'type',
                  'descrition', 'location', 'short_link',)

    def get_id(self, obj):
        return obj.image_video.id

    def get_teacher(self, obj):
        return 'dummy'

    def get_creation_date(self, obj):
        return obj.image_video.creation_date

    def get_type(self, obj):
        return obj.image_video.type

    def get_descrition(self, obj):
        return obj.image_video.descrition

    def get_short_link(self, obj):
        return obj.image_video.short_link

    def get_location(self, obj):
        return 'dummy'