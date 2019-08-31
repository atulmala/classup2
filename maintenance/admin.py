from django.contrib import admin

# Register your models here.

from .models import SMSDelStats, DailyMessageCount


class SMSDelAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'time_taken', 'messages_count',)


admin.site.register(SMSDelStats, SMSDelAdmin)


class DailyMessageCountAdmin(admin.ModelAdmin):
    list_display = ('date', 'school', 'message_count', 'sms_count',)
    list_filter = ('date', 'school',)
    search_fields = ('date',)


admin.site.register(DailyMessageCount, DailyMessageCountAdmin)
