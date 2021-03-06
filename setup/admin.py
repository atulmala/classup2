from django.contrib import admin
from .models import *

# Register your models here.


class SchoolAdmin(admin.ModelAdmin):
    list_display = ['id', 'school_name', 'subscription_active', 'school_address',]
    pass


admin.site.register(School, SchoolAdmin)


class ConfigurationsAdmin(admin.ModelAdmin):
    list_display = ('school', 'send_sms', 'include_welcome_sms', 'vendor_sms', 'vendor_bulk_sms',)


admin.site.register(Configurations, ConfigurationsAdmin)


class GlobalConfAdmin(admin.ModelAdmin):
    pass


admin.site.register(GlobalConf, GlobalConfAdmin)


class UserSchoolMappingAdmin(admin.ModelAdmin):
    list_display = ['user', 'school']
    list_filter = ['school',]
    search_fields = ['school__school_name',]


admin.site.register(UserSchoolMapping, UserSchoolMappingAdmin)


class SchoolGroupAdmin(admin.ModelAdmin):
    list_display = ['group_name',]


admin.site.register(SchoolGroup, SchoolGroupAdmin)


