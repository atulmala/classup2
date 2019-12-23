from rest_framework import serializers


from .models import SubjectAnalysis


class SubjectAnalysisSerializer(serializers.ModelSerializer):
    exam = serializers.StringRelatedField()
    subject = serializers.StringRelatedField()
    class Meta:
        model = SubjectAnalysis
        fields = ('id', 'exam', 'subject', 'marks', 'periodic_test_marks', 'multi_asses_marks', 'portfolio_marks',
                  'sub_enrich_marks', 'prac_marks', 'total_marks', )