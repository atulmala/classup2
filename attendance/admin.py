from django.contrib import admin

from .models import Attendance, AttendanceTaken
from student.models import Student
from academics.models import Class, Section, Subject

# Register your models here.


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'the_class', 'section', 'subject', 'student',)

admin.site.register(Attendance, AttendanceAdmin)


class AttendanceTakenAdmin(admin.ModelAdmin):
    list_display = ('date', 'the_class', 'section', 'subject', 'taken_by',)

admin.site.register(AttendanceTaken, AttendanceTakenAdmin)
