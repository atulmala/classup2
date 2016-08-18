from django.contrib import admin
from .models import *

# Register your models here.


class SchoolAdmin(admin.ModelAdmin):
    pass

admin.site.register(School, SchoolAdmin)


class ConfigurationsAdmin(admin.ModelAdmin):
    pass

admin.site.register(Configurations, ConfigurationsAdmin)


class UserSchoolMappingAdmin(admin.ModelAdmin):
    list_display = ['user', 'school']

admin.site.register(UserSchoolMapping, UserSchoolMappingAdmin)
