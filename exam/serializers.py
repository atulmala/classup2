from rest_framework import serializers

from academics.models import TermTestResult, TestResults
from .models import Wing, ExamResult, Compartment


class WingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wing
        fields = ('school', 'wing', 'classes')


class ExamResultSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    compartment_subjects = serializers.SerializerMethodField()

    class Meta:
        model = ExamResult
        fields = ('id', 'student', 'status', 'detain_reason', 'exact_status', 'compartment_subjects')

    def get_compartment_subjects(self, obj):
        try:
            compartments = Compartment.objects.filter(student=obj.student)
            subjects = ''
            if compartments.count() > 0:
                for compartment in compartments:
                    subjects += ' %s' % compartment.subject.subject_name
            return subjects
        except Exception as e:
            print('exception 15032020-A from exam serializers.py %s %s' % (e.message, type(e)))
            print('error in retrieving compartment')
            return ''


class TestMarksSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    parent = serializers.SerializerMethodField()
    periodic_test_marks = serializers.SerializerMethodField()
    multi_asses_marks = serializers.SerializerMethodField()
    notebook_marks = serializers.SerializerMethodField()
    sub_enrich_marks = serializers.SerializerMethodField()
    prac_marks = serializers.SerializerMethodField()

    class Meta:
        model = TestResults
        fields = ('id', 'roll_no', 'student', 'parent', 'marks_obtained', 'grade',
                  'periodic_test_marks', 'multi_asses_marks', 'notebook_marks',
                  'sub_enrich_marks', 'prac_marks')

    def get_parent(self, obj):
        return obj.student.parent.parent_name

    def get_notebook_marks(self, obj):
        try:
            term_test_result = TermTestResult.objects.get(test_result=obj)
            return term_test_result.note_book_marks
        except Exception as e:
            return "N/A"

    def get_periodic_test_marks(self, obj):
        try:
            term_test_result = TermTestResult.objects.get(test_result=obj)
            return term_test_result.periodic_test_marks
        except Exception as e:
            return "N/A"

    def get_multi_asses_marks(self, obj):
        try:
            term_test_result = TermTestResult.objects.get(test_result=obj)
            return term_test_result.multi_asses_marks
        except Exception as e:
            return "N/A"

    def get_sub_enrich_marks(self, obj):
        try:
            term_test_result = TermTestResult.objects.get(test_result=obj)
            return term_test_result.sub_enrich_marks
        except Exception as e:
            return "N/A"

    def get_prac_marks (self, obj):
        try:
            term_test_result = TermTestResult.objects.get(test_result=obj)
            return term_test_result.prac_marks
        except Exception as e:
            print ('exception 24122017-A from exam serializer Exception = %s %s' % (e.message, type(e)))

