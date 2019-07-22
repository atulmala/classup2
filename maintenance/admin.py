from django.contrib import admin

# Register your models here.

from .models import SMSDelStats


class SMSDelAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'time_taken', 'messages_count',)


admin.site.register(SMSDelStats, SMSDelAdmin)
