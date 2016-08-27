from django.contrib import admin

from .models import Attendance, AttendanceTaken
from student.models import Student
from academics.models import Class, Section, Subject

# Register your models here.


class AttendanceAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        c = Class.objects.get(id=obj.id)
        print(c)
        s = c.school
        print(s)

        return s.school_name
    get_school_name.short_description = 'School'
    list_display = ('date', 'get_school_name', 'the_class', 'section', 'subject', 'student',)

admin.site.register(Attendance, AttendanceAdmin)


class AttendanceTakenAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        c = Class.objects.get(id=obj.id)
        print(c)
        s = c.school
        print(s)

        return s.school_name
    get_school_name.short_description = 'School'

    list_display = ('date', 'get_school_name', 'the_class', 'section', 'subject', 'taken_by',)

admin.site.register(AttendanceTaken, AttendanceTakenAdmin)
