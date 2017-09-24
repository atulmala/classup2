__author__ = 'atulgupta'

from rest_framework import serializers

from .models import Class, Section, Subject, ClassTest, TestResults, TermTestResult, WorkingDays, Exam, HomeWork, HW


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
        fields = ('id', 'date_conducted', 'teacher', 'subject', 'the_class', 'section',
                  'max_marks', 'passing_marks', 'grade_based', 'is_completed', 'syllabus', 'test_type',)


class TestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassTest
        fields = ('grade_based', 'max_marks', 'passing_marks',)


class TestMarksSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    parent = serializers.SerializerMethodField()
    periodic_test_marks = serializers.SerializerMethodField()
    notebook_marks = serializers.SerializerMethodField()
    sub_enrich_marks = serializers.SerializerMethodField()

    class Meta:
        model = TestResults
        fields = ('id', 'roll_no', 'student', 'parent', 'marks_obtained', 'grade',
                  'periodic_test_marks', 'notebook_marks', 'sub_enrich_marks')

    def get_parent(self, obj):
        return obj.student.parent.parent_name

    def get_notebook_marks(self, obj):
        try:
            term_test_result = TermTestResult.objects.get(test_result=obj)
            return term_test_result.note_book_marks
        except Exception as e:
            print ('Failed to retrieve notebook marks. This is not a Term Test but a Unit Test')
            print ('Exception 10 from academics serializer Exception = %s (%s)' % (e.message, type(e)))
            return "N/A"

    def get_periodic_test_marks(self, obj):
        try:
            term_test_result = TermTestResult.objects.get(test_result=obj)
            return term_test_result.periodic_test_marks
        except Exception as e:
            print ('Failed to retrieve periodic test marks. This is not a Term Test but a Unit Test')
            print ('Exception 20 from academics serializer Exception = %s (%s)' % (e.message, type(e)))
            return "N/A"

    def get_sub_enrich_marks(self, obj):
        try:
            term_test_result = TermTestResult.objects.get(test_result=obj)
            return term_test_result.sub_enrich_marks
        except Exception as e:
            print ('Failed to retrieve subject enrichment test marks. This is not a Term Test but a Unit Test')
            print ('Exception 30 from academics serializer Exception = %s (%s)' % (e.message, type(e)))
            return "N/A"


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
        fields = ('id', 'teacher', 'the_class', 'section', 'subject', 'due_date', 'notes', 'location',)
