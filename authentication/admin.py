from django.contrib import admin
from .models import LoginRecord

# Register your models here.


class LoginRecordAdmin(admin.ModelAdmin):
    list_display = ('date_and_time', 'login_id', 'password', 'string_ip',
                    'ip_address', 'login_type', 'outcome', 'comments',)
    search_fields = ('login_id',)
    list_filter = ('date_and_time',)

admin.site.register(LoginRecord, LoginRecordAdmin)
