from django.contrib import admin
from .models import Student, Parent, DOB, AdditionalDetails

# Register your models here.


class StudentAdmin(admin.ModelAdmin):
    def get_parent_name(self, obj):
        return obj.parent
    get_parent_name.short_description = 'Parent'

    def get_school_name(self, obj):
        return obj.school
    get_school_name.short_description = 'School'

    search_fields = ['fist_name', 'last_name', 'student_erp_id',]
    list_display = ('student_erp_id', 'fist_name', 'last_name', 'school',
                    'current_class', 'current_section', 'get_parent_name', 'active_status',)
    list_filter = ('active_status', 'school', )


admin.site.register(Student, StudentAdmin)


class ParentAdmin(admin.ModelAdmin):
    search_fields = ['parent_name', 'parent_mobile1', 'parent_mobile2', 'parent_email',]
    list_display = ['parent_name', 'parent_mobile1', 'parent_mobile2', 'parent_email',]


admin.site.register(Parent, ParentAdmin)


class DOBAdmin(admin.ModelAdmin):
    list_display = ('student', 'dob',)
    search_fields = ('student__fist_name', 'student__last_name')
    list_filter = ('student__school',)


admin.site.register(DOB, DOBAdmin)


