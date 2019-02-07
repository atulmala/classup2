from django.contrib import admin

from academics.models import ThirdLang
from .models import Scheme, HigherClassMapping, NPromoted, Marksheet

# Register your models here.


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


class HigherClassMappingAdmin (admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school

    def get_class (self, obj):
        return obj.student.current_class
    get_class.short_description = 'Class'

    def get_section (self, obj):
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

    def get_class (self, obj):
        return obj.student.current_class
    get_class.short_description = 'Class'

    def get_section (self, obj):
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

