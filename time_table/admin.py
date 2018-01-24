from django.contrib import admin

from .models import *

# Register your models here.


class WingAdmin (admin.ModelAdmin):
    list_display = ('school', 'wing', 'start_class', 'end_class',)


admin.site.register(Wing, WingAdmin)


class DaysOfWeekAdmin (admin.ModelAdmin):
    list_display = ('day', 'sequence',)


admin.site.register(DaysOfWeek, DaysOfWeekAdmin)


class PeriodAdmin (admin.ModelAdmin):
    list_display = ('school', 'period', 'start_time', 'end_time',)


admin.site.register(Period, PeriodAdmin)


class TimeTableAdmin (admin.ModelAdmin):
    list_display = ('school', 'day', 'period', 'the_class', 'section', 'period', 'subject', 'teacher',)
    search_fields = ('teacher__first_name',)


admin.site.register (TimeTable, TimeTableAdmin)


class TeacherPeriodsAdmin (admin.ModelAdmin):
    list_display = ('school', 'day', 'the_class', 'section', 'period', 'teacher',)
    list_filter = ('day',)
    search_fields = ('teacher__first_name', 'teacher__last_name',)


admin.site.register(TeacherPeriods, TeacherPeriodsAdmin)


class ExcludedFromArrangementsAdmin (admin.ModelAdmin):
    list_display = ('school', 'teacher',)


admin.site.register(ExcludedFromArrangements1, ExcludedFromArrangementsAdmin)


class TeacherWingMappingAdmin (admin.ModelAdmin):
    list_display = ('school', 'teacher', 'wing',)
    search_fields = ('teacher__first_name', 'teacher__last_name',)
    list_filter = ('school',)


admin.site.register(TeacherWingMapping, TeacherWingMappingAdmin)


class ArrangementAdmin (admin.ModelAdmin):
    list_display = ('school', 'date', 'the_class', 'section', 'period', 'subject', 'teacher',)


admin.site.register(Arrangements, ArrangementAdmin)
