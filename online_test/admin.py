from django.contrib import admin

# Register your models here.

from .models import OnlineTest, OnlineQuestion, StudentTestAttempt, StudentQuestion, AnswerSheets


@admin.register(OnlineTest)
class OnlineTestAdmin(admin.ModelAdmin):
    list_display = ('school', 'exam', 'the_class', 'subject', 'teacher', 'date', 'duration',)
    list_filter = ('school',)


@admin.register(OnlineQuestion)
class OnlineQuestionAdmin(admin.ModelAdmin):
    list_display = ('question',)


@admin.register(StudentTestAttempt)
class StudentTestAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'online_test', 'date',)
    search_fields = ('student__fist_name', 'student__last_name', )


@admin.register(StudentQuestion)
class StudentQuestionAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'answer_marked', 'whether_correct',)


@admin.register(AnswerSheets)
class AnswerSheetsAdmin(admin.ModelAdmin):
    list_display = ('student', 'online_test', 'link',)
    search_fields = ('student__fist_name', 'student__last_name',)
