from django.contrib import admin

from academics.models import ThirdLang
from .models import Scheme, HigherClassMapping

# Register your models here.


class ThirdLangAdmin(admin.ModelAdmin):
    list_display = ('student', 'third_lang',)


admin.site.register(ThirdLang, ThirdLangAdmin)


class SchemeAdmin(admin.ModelAdmin):
    list_display = ('school', 'the_class', 'sequence', 'subject', 'subject_type',)


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
    list_display = ('get_school_name', 'get_class', 'get_section', 'student', 'subject',)


admin.site.register(HigherClassMapping, HigherClassMappingAdmin)
