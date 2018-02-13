from django.contrib import admin
from .models import *

# Register your models here.


class SectionAdmin(admin.ModelAdmin):
    list_display = ['school', 'section']
    list_filter = ['school']


admin.site.register(Section, SectionAdmin)


class ClassAdmin(admin.ModelAdmin):
    list_display = ['school', 'standard']
    list_filter = ['school']


admin.site.register(Class, ClassAdmin)


class SubjectAdmin(admin.ModelAdmin):
    search_fields = ['subject_name']
    list_display = ['school', 'subject_name', 'subject_code', 'subject_type',]
    list_filter = ['school',]


admin.site.register(Subject, SubjectAdmin)


class TestAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.the_class.school
    get_school_name.short_description = 'School'

    def get_class(self, obj):
        return obj.the_class.standard + '-' + obj.section.section
    get_class.short_description = 'Class'

    def get_subject(self, obj):
        return obj.subject
    get_subject.short_description = 'Subject'

    list_display = ('get_school_name', 'get_class', 'subject', 'teacher', 'date_conducted', 'test_type', 'max_marks',
                    'passing_marks', 'is_completed', )

    list_filter = ('the_class__school',)

    search_fields = ('subject__subject_name', 'the_class__standard', 'section__section', )


admin.site.register(ClassTest, TestAdmin)


class TestResultsAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.class_test.the_class.school.school_name
    get_school_name.short_description = 'School'

    def get_class(self, obj):
        return obj.class_test.the_class.standard + '-' + obj.class_test.section.section
    get_class.short_description = 'Class'

    def get_subject(self, obj):
        return obj.class_test.subject
    get_subject.short_description = 'Subject'

    def get_date(self, obj):
        return obj.class_test.date_conducted
    get_date.short_description = 'Date Conducted'

    def get_max_marks(self, obj):
        return obj.class_test.max_marks
    get_max_marks.short_description = 'Max Marks'

    list_display = ('get_school_name', 'get_class', 'get_subject', 'get_date', 'student', 'get_max_marks',
                    'marks_obtained', 'grade',)


admin.site.register(TestResults, TestResultsAdmin)


class CoScholasticAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.the_class.school.school_name
    get_school_name.short_description = 'School'

    def get_student(self, obj):
        return obj.student
    get_student.short_description = 'Student'

    def get_class(self, obj):
        return obj.the_class.standard + '-' + obj.section.section
    get_class.short_description = 'Class'

    list_display = ('get_school_name', 'get_class', 'get_student', 'term', 'work_education', 'art_education',
                    'health_education', 'discipline', 'teacher_remarks', 'promoted_to_class',)


admin.site.register(CoScholastics, CoScholasticAdmin)


class TermTestResultsAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.test_result.class_test.the_class.school.school_name
    get_school_name.short_description = 'School'

    def get_student(self, obj):
        return obj.test_result.student
    get_student.short_description = 'Student'

    def get_class(self, obj):
        return obj.test_result.class_test.the_class.standard + '-' + obj.test_result.class_test.section.section
    get_class.short_description = 'Class'

    def get_subject(self, obj):
        return obj.test_result.class_test.subject
    get_subject.short_description = 'Subject'

    def get_date(self, obj):
        return obj.test_result.class_test.date_conducted
    get_date.short_description = 'Date Conducted'

    def get_max_marks(self, obj):
        return obj.test_result.class_test.max_marks
    get_max_marks.short_description = 'Max Marks'

    def get_marks_obtained(self, obj):
        return obj.test_result.marks_obtained
    get_marks_obtained.short_description = "Marks Obtained"

    list_display = ('get_school_name', 'get_class', 'get_subject', 'get_date', 'get_student', 'get_max_marks',
                    'get_marks_obtained',)
    search_fields = ('test_result__student__student_erp_id', 'test_result__student__fist_name',
                     'test_result__student__last_name',)


admin.site.register(TermTestResult, TermTestResultsAdmin)


class TeacherSubjectAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.teacher.school
    get_school_name.short_description = 'School'

    list_display = ('get_school_name', 'teacher', 'subject',)


admin.site.register(TeacherSubjects, TeacherSubjectAdmin)


class WorkingDaysAdmin(admin.ModelAdmin):
    pass


admin.site.register(WorkingDays, WorkingDaysAdmin)


class ClassTeacherAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.school
    get_school_name.short_description = 'School'

    def get_class(self, obj):
        return obj.standard.standard + '-' + obj.section.section
    get_class.short_description = 'Class'

    def get_class_teacher(self, obj):
        return obj.class_teacher
    get_class_teacher.short_name = 'Class Teacher'

    list_display = ('get_school_name', 'get_class', 'get_class_teacher',)
    list_filter = ('school', )


admin.site.register(ClassTeacher, ClassTeacherAdmin)


class ExamAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.school
    get_school_name.short_description = 'School'

    list_display = ('school', 'title', 'start_date', 'end_date', 'start_class', 'end_class',)


admin.site.register(Exam, ExamAdmin)


class HWAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.school
    get_school_name.short_description = 'School'

    list_display = ('school', 'teacher', 'the_class', 'section', 'subject',
                    'due_date', 'creation_date', 'uploaded_at', 'location',)

    fields = ('image_tag',)
    readonly_fields = ('image_tag',)


admin.site.register(HW, HWAdmin)









