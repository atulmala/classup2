from django.contrib import admin

# Register your models here.
from .models import SMSRecord

class SMSRecordAdmin(admin.ModelAdmin):
    list_display = ('school', 'sender1', 'sender_type', 'date',
                    'recipient_name', 'recipient_number', 'recipient_type', 'message', 'message_type', 'outcome',
                    'status_extracted', 'status',)
    list_filter = ('school', 'date')

admin.site.register(SMSRecord, SMSRecordAdmin)
