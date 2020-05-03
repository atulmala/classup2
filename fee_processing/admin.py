from django.contrib import admin

# Register your models here.
from fee_processing.models import FeeDefaulters


@admin.register(FeeDefaulters)
class FeeDefaultersAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school.school_name

    def get_class(self, obj):
        return obj.student.current_class

    def get_section(self, obj):
        return obj.student.current_section

    list_display = ('get_school_name', 'student', 'get_class',
                    'get_section', 'amount_due', 'stop_access',)
    list_filter = ('student__school',)
    search_fields = ('student__fist_name', 'student_last_name', )
