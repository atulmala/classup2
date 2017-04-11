__author__ = 'atulgupta'

from rest_framework import serializers

from .models import Class, Section, Subject, ClassTest, TestResults, WorkingDays, Exam, HomeWork, HW


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ('standard', 'sequence',)


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ('section', )


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('subject_name', 'subject_code', 'subject_sequence')


class TestSerializer(serializers.ModelSerializer):

    subject = serializers.StringRelatedField()
    the_class = serializers.StringRelatedField()
    section = serializers.StringRelatedField()

    class Meta:
        model = ClassTest
        fields = ('id', 'date_conducted', 'teacher', 'subject', 'the_class',
                  'section', 'max_marks', 'passing_marks', 'grade_based', 'is_completed', 'test_type',)


class TestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassTest
        fields = ('grade_based', 'max_marks', 'passing_marks',)


class TestMarksSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()

    class Meta:
        model = TestResults
        fields = ('id', 'roll_no', 'student', 'marks_obtained', 'grade',)


# serializer to return the class and section of test
class ClassSectionForTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassTest
        fields = ('the_class', 'section',)


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ('id', 'title', 'start_date', 'end_date',)


class WorkingDaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingDays
        fields = ('working_days',)


class HomeWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeWork
        fields = ('id', 'teacher', 'the_class', 'section', 'subject', 'due_date', 'notes')


class HWSerializer(serializers.ModelSerializer):
    class Meta:
        model=HW
        fields = ('id', 'teacher', 'the_class', 'section', 'subject', 'due_date', 'notes')
