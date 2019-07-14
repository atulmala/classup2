from django.contrib import admin

# Register your models here.
from .models import SMSRecord, ClassUpAdmin, SMSVendor, ParanShabd


class SMSRecordAdmin(admin.ModelAdmin):
    list_display = ('school', 'sender1', 'sender_type', 'date',
                    'recipient_name', 'recipient_number', 'recipient_type', 'message', 'message_type',
                    'the_vendor', 'api_called', 'outcome', 'status_extracted', 'status',)
    list_filter = ('date', 'status_extracted', 'api_called', 'school',)
    search_fields = ('recipient_number', 'recipient_name', 'message', 'status', 'outcome',)


admin.site.register(SMSRecord, SMSRecordAdmin)


class ClassUpAdminAdmin(admin.ModelAdmin):
    list_display = ('admin_mobile',)


admin.site.register(ClassUpAdmin, ClassUpAdminAdmin)


class VendorAdmin(admin.ModelAdmin):
    list_display = ('vendor',)


admin.site.register(SMSVendor, VendorAdmin)


class ParanShabdAdmin(admin.ModelAdmin):
    list_display = ('upbhokta', 'name', 'shabd',)
    search_fields = ('upbhokta', 'name',)


admin.site.register(ParanShabd, ParanShabdAdmin)