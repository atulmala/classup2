__author__ = 'atulgupta'


from rest_framework import serializers

from erp.models import CollectAdmFee
from .models import Student, Parent


class StudentSerializer(serializers.ModelSerializer):
    # we use SlugRelatedField because current_class and current_section are foreign keys in Student Model. Not using
    # slug related field would return the primary key instead of their respective names
    current_class = serializers.SlugRelatedField(read_only=True, slug_field='standard')
    current_section = serializers.SlugRelatedField(read_only=True, slug_field='section')
    parent =  serializers.SlugRelatedField(read_only=True, slug_field='parent_name')

    class Meta:
        model = Student
        fields = ('id', 'student_erp_id', 'fist_name', 'last_name',
                  'roll_number', 'current_class', 'current_section', 'parent')


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ('parent_name', 'parent_mobile1', 'parent_mobile2',)

