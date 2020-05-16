from django.contrib import admin

# Register your models here.

from .models import OnlineTest, OnlineQuestion, StudentTestAttempt, StudentQuestion, AnswerSheets

admin.autodiscover()


@admin.register(OnlineTest)
class OnlineTestAdmin(admin.ModelAdmin):
    list_display = ('school', 'exam', 'the_class', 'subject', 'teacher', 'date', 'duration',)
    list_filter = ('school',)


@admin.register(OnlineQuestion)
class OnlineQuestionAdmin(admin.ModelAdmin):
    def get_the_class(self, obj):
        return obj.test.the_class

    def get_date(self, obj):
        return obj.test.date

    def get_subject(self, obj):
        return obj.test.subject

    list_display = ('get_the_class', 'get_subject', 'get_date', 'question',)
    list_filter = ('test__date', 'test__school',)


@admin.register(StudentTestAttempt)
class StudentTestAttemptAdmin(admin.ModelAdmin):
    def get_school(self, obj):
        return obj.student.school

    def get_class(self, obj):
        return obj.student.current_class

    def get_section(self, obj):
        return obj.student.current_section

    def get_subject(self, obj):
        return obj.online_test.subject

    list_display = ('get_school', 'student', 'get_class', 'get_section',
                    'get_subject', 'date', 'submission_ok',)
    search_fields = ('student__fist_name', 'student__last_name',)
    list_filter = ('date', 'submission_ok',)


@admin.register(StudentQuestion)
class StudentQuestionAdmin(admin.ModelAdmin):
    def get_class(self, obj):
        return obj.question.test.the_class

    def get_subject(self, obj):
        return obj.question.test.subject

    list_display = ('student', 'get_class', 'get_subject', 'answer_marked', 'whether_correct',)
    search_fields = ('student__fist_name', 'student__last_name',)
    list_filter = ('answer_marked', 'question__test__date',)


@admin.register(AnswerSheets)
class AnswerSheetsAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school

    def get_class(self, obj):
        return obj.student.current_class

    def get_section(self, obj):
        return obj.student.current_section

    def get_subject(self, obj):
        return obj.online_test.subject

    def get_exam(self, obj):
        return obj.online_test.exam

    def get_date(self, obj):
        return obj.online_test.date

    list_display = ('get_date', 'get_school_name', 'student', 'get_class',
                    'get_section', 'get_subject', 'get_exam', 'link', 'shared',)
    search_fields = ('student__fist_name', 'student__last_name', 'online_test__subject__subject_name',)

    def link(self, obj):
        return '<a href="%s">%s</a>' % (obj.lin, obj.link)

    link.allow_tags = True
    link.short_description = 'Short link'
