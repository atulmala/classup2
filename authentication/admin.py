from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import LoginRecord, LastPasswordReset, user_device_mapping, log_book

# Register your models here.

class MyUserAdmin(UserAdmin):
    ordering = ('-date_joined',)
    list_display = ('username', 'date_joined', 'first_name', 'last_name',)
    list_filter = ('date_joined',)

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)


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
    search_fields = ('mobile_number',)

admin.site.register(user_device_mapping, UserDeviceMappingAdmin)


class LogBookAdmin(admin.ModelAdmin):
    list_display = ('date_and_time', 'user', 'school', 'user_name', 'event', 'category', 'outcome',)
    search_fields = ('user', 'user_name',)
    list_filter = ('date_and_time',)

admin.site.register(log_book, LogBookAdmin)
