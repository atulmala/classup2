from django.contrib import admin

# Register your models here.
from .models import SubjectAnalysis, SubjectHighestAverage, ExamHighestAverage, StudentTotalMarks


@admin.register(StudentTotalMarks)
class StudentTotalMarksAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school
    get_school_name.short_description = 'School'

    def get_class(self, obj):
        return '%s-%s' % (obj.student.current_class, obj.student.current_section)
    get_class.short_description = 'Class'

    list_display = ('get_school_name', 'student', 'get_class', 'exam', 'total_marks',)
    list_filter = ('student__school',)
    search_fields = ('student__fist_name', 'student__current_class__standard')


@admin.register(ExamHighestAverage)
class ExamHighestAverageAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school
    get_school_name.short_description = 'School'

    list_display = ('get_school_name', 'exam', 'the_class', 'section', 'highest', 'average',)
    list_filter = ('the_class__school',)


@admin.register(SubjectHighestAverage)
class SubjectHighestAverageAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.the_class.school
    get_school_name.short_description = 'School'

    list_display = ('get_school_name', 'the_class', 'section', 'subject', 'highest', 'average',)
    list_filter = ('the_class__school',)
    search_fields = ('subject__subject_name', 'the_class__standard',)


@admin.register(SubjectAnalysis)
class SubjectAnalysisAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school
    get_school_name.short_description = 'School'

    def get_class(self, obj):
        return obj.student.current_class.standard + '-' + obj.student.current_section.section
    get_class.short_description = 'Class'

    list_display = ('get_school_name', 'exam', 'student', 'get_class', 'subject', 'marks', 'periodic_test_marks',
                    'multi_asses_marks', 'portfolio_marks', 'sub_enrich_marks',
                    'prac_marks', 'total_marks', 'highest', 'average',)
    list_filter = ('student__school',)
    search_fields = ('student__fist_name', 'student__last_name', 'subject__subject_name')


