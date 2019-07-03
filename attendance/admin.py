from django.contrib import admin

from .models import Attendance, AttendanceTaken, AttendanceUpdated

# Register your models here.


class AttendanceAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.the_class.school
    get_school_name.short_description = 'School'
    list_display = ('date', 'get_school_name', 'the_class', 'section', 'subject', 'taken_by', 'student',)
    list_filter = ('the_class__school', 'date',)
    search_fields = ('student__fist_name', 'student__last_name')


admin.site.register(Attendance, AttendanceAdmin)


class AttendanceTakenAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.the_class.school
    get_school_name.short_description = 'School'

    list_display = ('date', 'get_school_name', 'the_class', 'section',
                    'subject', 'taken_by', 'taken_time',)
    list_filter = ('date', 'the_class__school',)


admin.site.register(AttendanceTaken, AttendanceTakenAdmin)


class AttendanceUpdateAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.the_class.school
    get_school_name.short_description = 'School'

    list_display = ('date', 'get_school_name', 'the_class', 'section',
                    'subject', 'updated_by', 'update_date_time',)
    list_filter = ('date',)

admin.site.register(AttendanceUpdated, AttendanceUpdateAdmin)
