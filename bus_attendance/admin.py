from django.contrib import admin

# Register your models here.

from teacher.models import Teacher
from .models import Bus_Attendance, Attedance_Type, Student_Rout, Bus_Rout, BusAttendanceTaken, BusStop


class BusAttendanceAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        rout = Bus_Rout.objects.get(id=obj.bus_rout.id)
        school = rout.school
        return school.school_name
    get_school_name.short_description = 'School'

    list_display = ('date', 'get_school_name', 'bus_rout', 'attendance_type', 'student',)
    search_fields = ('student__fist_name',)

admin.site.register(Bus_Attendance, BusAttendanceAdmin)


class AttendanceTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(Attedance_Type, AttendanceTypeAdmin)


class StudentRoutAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        rout = Bus_Rout.objects.get(id=obj.bus_root.id)
        school = rout.school
        return school.school_name
    get_school_name.short_description = 'School'
    list_display = ('student', 'get_school_name', 'bus_root', 'bus_stop', )
    search_fields = ('student__fist_name',)

admin.site.register(Student_Rout, StudentRoutAdmin)


class BusRoutAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        rout = Bus_Rout.objects.get(id=obj.id)
        school = rout.school
        return school.school_name
    get_school_name.short_description = 'School'
    list_display = ('get_school_name', 'bus_root', )
    search_fields = ('school__school_name',)

admin.site.register(Bus_Rout, BusRoutAdmin)


class BusAttendanceTakenAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        rout = Bus_Rout.objects.get(id=obj.rout.id)
        school = rout.school
        return school.school_name

    def get_teacher_name(self, obj):
        t = Teacher.objects.get(id=obj.taken_by.id)
        teacher = t.first_name = ' ' + t.last_name
        return teacher

    get_school_name.short_description = 'School'
    get_teacher_name.short_description = 'Teacher'

    list_display = ('date', 'get_school_name', 'rout', 'type', 'taken_by',)


admin.site.register(BusAttendanceTaken, BusAttendanceTakenAdmin)


class BusStopAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        rout = Bus_Rout.objects.get(id=obj.bus_rout.id)
        school = rout.school
        return school.school_name
    get_school_name.short_description = 'School'
    list_display = ('get_school_name', 'bus_rout', 'stop_name')
    search_fields = ('stop_name', 'bus_rout__bus_root')

admin.site.register(BusStop, BusStopAdmin)
