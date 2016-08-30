from django.contrib import admin

from .models import *

# Register your models here.


class TeacherAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name']
    list_display = ['first_name', 'last_name', 'teacher_erp_id', 'school']

admin.site.register(Teacher, TeacherAdmin)