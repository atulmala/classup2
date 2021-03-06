from django.contrib import admin

from .models import *

# Register your models here.


class TeacherAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name']
    list_display = ['first_name', 'last_name', 'teacher_erp_id', 'email', 'school']
    list_filter = ('school', )


admin.site.register(Teacher, TeacherAdmin)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name']
    list_display = ['first_name', 'last_name', 'staff_erp_id', 'email', 'school']
    list_filter = ('school', )


class TeacherAttendanceTakenAdmin(admin.ModelAdmin):
    list_display = ('school', 'date', 'taken_time',)


admin.site.register(TeacherAttendnceTaken, TeacherAttendanceTakenAdmin)


class TeacherAttendanceAdmin (admin.ModelAdmin):
    list_display = ('school', 'teacher', 'date',)


admin.site.register(TeacherAttendance, TeacherAttendanceAdmin)


class TeacherMessageRecordAdmin (admin.ModelAdmin):
    list_display = ('date', 'teacher', 'message', 'sent_to', 'the_class', 'section', 'activity_group')


admin.site.register (TeacherMessageRecord, TeacherMessageRecordAdmin)


class MessageReceiversAdmin (admin.ModelAdmin):
    list_display = ('date', 'student', 'full_message', 'status', 'status_extracted', 'outcome',)


admin.site.register (MessageReceivers, MessageReceiversAdmin)