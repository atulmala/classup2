from django.contrib import admin

# Register your models here.

from .models import OnlineTest, OnlineQuestion


@admin.register(OnlineTest)
class OnlineTestAdmin(admin.ModelAdmin):
    list_display = ('school', 'the_class', 'subject', 'teacher', 'date', 'duration',)
    list_filter = ('school',)


@admin.register(OnlineQuestion)
class OnlineQuestionAdmin(admin.ModelAdmin):
    list_display = ('question',)
