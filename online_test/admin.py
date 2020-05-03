from django.contrib import admin

# Register your models here.

from .models import OnlineTest, OnlineQuestion, StudentTestAttempt, StudentQuestion, AnswerSheets


@admin.register(OnlineTest)
class OnlineTestAdmin(admin.ModelAdmin):
    list_display = ('school', 'exam', 'the_class', 'subject', 'teacher', 'date', 'duration',)
    list_filter = ('school',)


@admin.register(OnlineQuestion)
class OnlineQuestionAdmin(admin.ModelAdmin):
    def get_the_class(self, obj):
        return obj.test.the_class

    def get_subject(self, obj):
        return obj.test.subject
    list_display = ('get_the_class', 'get_subject', 'question',)


@admin.register(StudentTestAttempt)
class StudentTestAttemptAdmin(admin.ModelAdmin):
    def get_school(self, obj):
        return obj.student.school

    def get_class(self, obj):
        return obj.student.current_class

    def get_section(self, obj):
        return obj.student.current_section

    list_display = ('get_school', 'student', 'get_class', 'get_section', 'online_test', 'date',)
    search_fields = ('student__fist_name', 'student__last_name', )


@admin.register(StudentQuestion)
class StudentQuestionAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'answer_marked', 'whether_correct',)


@admin.register(AnswerSheets)
class AnswerSheetsAdmin(admin.ModelAdmin):
    list_display = ('student', 'online_test', 'link', 'shared',)
    search_fields = ('student__fist_name', 'student__last_name',)

    def link(self, obj):
        return '<a href="%s">%s</a>' % (obj.lin, obj.link)
    link.allow_tags = True
    link.short_description = 'Short link'


