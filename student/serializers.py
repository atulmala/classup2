__author__ = 'atulgupta'


from rest_framework import serializers

from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    # we use SlugRelatedField because current_class and current_section are foreign keys in Student Model. Not using
    # slug related field would return the primary key instead of their respective names
    current_class = serializers.SlugRelatedField(read_only=True, slug_field='standard')
    current_section = serializers.SlugRelatedField(read_only=True, slug_field='section')

    class Meta:
        model = Student
        fields = ('id', 'fist_name', 'last_name', 'roll_number', 'current_class', 'current_section',)