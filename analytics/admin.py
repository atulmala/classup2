from django.contrib import admin

# Register your models here.
from .models import SubjectAnalysis


class SubjectAnalysisAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.the_class.school
    get_school_name.short_description = 'School'

    def get_class(self, obj):
        return obj.the_class.standard + '-' + obj.section.section
    get_class.short_description = 'Class'

    list_display = ('get_school_name', 'student', 'get_class', 'subject', 'marks', 'highest', 'average',)
    list_filter = ('student__school',)


admin.site.register(SubjectAnalysis, SubjectAnalysisAdmin)
