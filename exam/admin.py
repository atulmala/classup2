from django.contrib import admin

from academics.models import ThirdLang
from .models import Scheme, HigherClassMapping, NPromoted, Marksheet, Stream, StreamMapping, Wing, ExamResult, \
    Compartment
from .models import CBSERollNo


# Register your models here.


class StreamAdmin(admin.ModelAdmin):
    list_display = ('stream',)


admin.site.register(Stream, StreamAdmin)


class StreamMappingAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school

    get_school_name.short_description = 'School'
    search_fields = ('student__fist_name',)
    list_display = ('get_school_name', 'student', 'stream',)
    list_filter = ('stream', 'student__school',)


admin.site.register(StreamMapping, StreamMappingAdmin)


class ThirdLangAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school.school_name

    get_school_name.short_description = 'School'

    def get_class(self, obj):
        return '%s-%s' % (obj.student.current_class.standard, obj.student.current_section.section)

    get_class.short_description = 'Class'

    list_display = ('student', 'get_class', 'third_lang', 'get_school_name',)
    list_filter = ('student__school',)

    search_fields = ('student__fist_name',)


admin.site.register(ThirdLang, ThirdLangAdmin)


class SchemeAdmin(admin.ModelAdmin):
    list_display = ('school', 'the_class', 'sequence', 'subject', 'subject_type',)
    list_filter = ('school',)


admin.site.register(Scheme, SchemeAdmin)


class HigherClassMappingAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school

    def get_class(self, obj):
        return obj.student.current_class

    get_class.short_description = 'Class'

    def get_section(self, obj):
        return obj.student.current_section

    get_section.short_description = 'Section'

    get_school_name.short_description = 'School'
    search_fields = ('student__fist_name',)
    list_display = ('get_school_name', 'get_class', 'get_section', 'student', 'subject',)
    list_filter = ('student__school',)


admin.site.register(HigherClassMapping, HigherClassMappingAdmin)


class NotPromotedAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school

    def get_class(self, obj):
        return obj.student.current_class

    get_class.short_description = 'Class'

    def get_section(self, obj):
        return obj.student.current_section

    get_section.short_description = 'Section'

    get_school_name.short_description = 'School'
    search_fields = ('student__fist_name',)
    list_display = ('get_school_name', 'student', 'get_class', 'get_section', 'details',)
    list_filter = ('student__school',)


admin.site.register(NPromoted, NotPromotedAdmin)


class MarksheetAdmin(admin.ModelAdmin):
    list_display = ('school', 'title_start', 'address_start', 'place', 'result_date',)
    list_filter = ('school',)


admin.site.register(Marksheet, MarksheetAdmin)


class WingAdmin(admin.ModelAdmin):
    list_display = ('school', 'wing', 'classes')
    list_filter = ('school',)


admin.site.register(Wing, WingAdmin)


@admin.register(Compartment)
class CompartmentAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school

    list_display = ('get_school_name', 'student', 'subject',)
    list_filter = ('student__school',)
    search_fields = ('student__fist_name', 'student__last_name',)


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school

    list_display = ('get_school_name', 'student', 'status', 'detain_reason',)
    list_filter = ('student__school', 'status',)
    search_fields = ('student__fist_name', 'student__last_name',)


@admin.register(CBSERollNo)
class CBSERollNoAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school

    list_display = ('get_school_name', 'student', 'cbse_roll_no')
    list_filter = ('student__school',)
    search_fields = ('student__fist_name', 'student__last_name',)
