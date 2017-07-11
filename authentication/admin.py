from django.contrib import admin
from .models import LoginRecord, LastPasswordReset, user_device_mapping

# Register your models here.


class LoginRecordAdmin(admin.ModelAdmin):
    list_display = ('date_and_time', 'login_id', 'password', 'string_ip',
                    'ip_address', 'login_type', 'model', 'os', 'resolution', 'size', 'outcome', 'comments',)
    search_fields = ('login_id',)
    list_filter = ('date_and_time',)

admin.site.register(LoginRecord, LoginRecordAdmin)


class LastPasswordResetAdmin(admin.ModelAdmin):
    list_display = ('login_id', 'last_reset_time',)
    search_fields = ('login_id', 'last_reset_time',)

admin.site.register(LastPasswordReset, LastPasswordResetAdmin)


class UserDeviceMappingAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'token_id', 'device_type',)

admin.site.register(user_device_mapping, UserDeviceMappingAdmin)
