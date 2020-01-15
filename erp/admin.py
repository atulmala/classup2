from django.contrib import admin
from student.models import AdditionalDetails, House
from .models import CollectAdmFee, FeePaymentHistory, PreviousBalance, ReceiptNumber, HeadWiseFee, FeeCorrection
from .models import CollectTransportFee, TransportSlab

# Register your models here.


class AdditionalDetailsAdmin(admin.ModelAdmin):
    def get_house(self, obj):
        try:
            h = House.objects.get(student=obj.student)
            return h.house
        except Exception as e:
            print('exception 28032018-A from erp admin.py %s %s' % (e.message, type(e)))
            print('house for %s not yet set' % obj.student.student_erp_id)
            na = 'Not Available'
            return na
    list_display = ('student', 'mother_name', 'address', 'get_house')
    search_fields = ('student__fist_name', 'student__last_name')
    list_filter = ('student__school',)


admin.site.register(AdditionalDetails, AdditionalDetailsAdmin)


@admin.register(CollectTransportFee)
class CollectTransportFeeAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school

    get_school_name.short_description = 'School'

    list_display = ('get_school_name', 'student', 'bus_fee', 'slab',)
    search_fields = ('student__fist_name', 'student__last_name')
    list_filter = ('student__school',)


@admin.register(TransportSlab)
class TransportSlabAdmin(admin.ModelAdmin):
    list_display = ('school', 'slab', 'amount',)
    list_filter = ('school',)
    search_fields = ('slab',)


class CollectAdmFeeAdmin(admin.ModelAdmin):
    list_display = ('school', 'student', 'whether_paid',)
    search_fields = ('student__fist_name', 'student__last_name',)
    list_filter = ('school', 'whether_paid',)


admin.site.register(CollectAdmFee, CollectAdmFeeAdmin)


class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('date', 'school', 'parent', 'student', 'data', 'amount', 'fine', 'one_time', 'discount',
                    'waiver', 'receipt_number', 'mode', 'cheque_number', 'bank',)
    search_fields = ('student', 'receipt_number',)
    list_filter = ('school',)


admin.site.register(FeePaymentHistory, FeePaymentAdmin)


class PreviousBalanceAdmin(admin.ModelAdmin):
    list_display = ('school', 'parent', 'student', 'due_amount', 'negative',)
    search_fields = ('student',)
    list_filter = ('school',)


admin.site.register(PreviousBalance, PreviousBalanceAdmin)


class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('school', 'start_receipt')
    list_filter = ('school',)


admin.site.register(ReceiptNumber, ReceiptAdmin)


class FeeHeadsAdmin(admin.ModelAdmin):
    list_display = ('date', 'school', 'student', 'PaymentHistory', 'head', 'amount')
    search_fields = ('student', 'head',)
    list_filter = ('school', 'head',)


admin.site.register(HeadWiseFee, FeeHeadsAdmin)


class FeeCorrectionAdmin(admin.ModelAdmin):
    list_display = ('date', 'school', 'receipt_number', 'amount', 'fine', 'one_time', 'discount',)
    search_fields = ('receipt_number',)
    list_filter = ('school',)


admin.site.register(FeeCorrection, FeeCorrectionAdmin)

