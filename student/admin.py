from django.contrib import admin
from setup.models import School
from .models import Student, Parent

# Register your models here.


class StudentAdmin(admin.ModelAdmin):
    def get_parent_name(self, obj):
        p = Parent.objects.get(id=obj.id)
        return p
    get_parent_name.short_description = 'Parent'

    def get_school_name(self, obj):
        s = School.objects.get(id=obj.id)

        return s.school_name
    get_school_name.short_description = 'School'

    search_fields = ['fist_name', 'last_name']
    list_display = ('fist_name', 'last_name', 'school',
                    'current_class', 'current_section', 'get_parent_name',)

admin.site.register(Student, StudentAdmin)

class ParentAdmin(admin.ModelAdmin):
    #def get_student_name(self, obj):
        #full_name = obj.student_id.fist_name + ' ' + obj.student_id.last_name
        #return full_name
    #get_student_name.short_description = 'Student Name'
    search_fields = ['parent_name']
    list_display = ['parent_name', 'parent_mobile1', 'parent_mobile2', 'parent_email']

admin.site.register(Parent, ParentAdmin)
