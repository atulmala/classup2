from django.contrib import admin

from .models import *

# Register your models here.


class TeacherAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name']

admin.site.register(Teacher, TeacherAdmin)