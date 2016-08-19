from django.contrib import admin
from .models import *

# Register your models here.


class SectionAdmin(admin.ModelAdmin):
    list_display = ['school', 'section']

admin.site.register(Section, SectionAdmin)


class ClassAdmin(admin.ModelAdmin):
    list_display = ['standard']

admin.site.register(Class, ClassAdmin)


class SubjectAdmin(admin.ModelAdmin):
    search_fields = ['subject_name']
    list_display = ['school', 'subject_name', 'subject_code']

admin.site.register(Subject, SubjectAdmin)


class TestAdmin(admin.ModelAdmin):
    pass

admin.site.register(ClassTest, TestAdmin)


class TestResultsAdmin(admin.ModelAdmin):
    pass

admin.site.register(TestResults, TestResultsAdmin)


class TeacherSubjectAdmin(admin.ModelAdmin):
    pass

admin.site.register(TeacherSubjects, TeacherSubjectAdmin)


class WorkingDaysAdmin(admin.ModelAdmin):
    pass

admin.site.register(WorkingDays, WorkingDaysAdmin)


class ClassTeacherAdmin(admin.ModelAdmin):
    pass

admin.site.register(ClassTeacher, ClassTeacherAdmin)


class ExamAdmin(admin.ModelAdmin):
    pass

admin.site.register(Exam, ExamAdmin)

