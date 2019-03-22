from django.contrib import admin
from student.models import AdditionalDetails, House
from .models import CollectAdmFee

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


class CollectAdmFeeAdmin(admin.ModelAdmin):
    list_display = ('school', 'student',)
    search_fields = ('school', 'student')
    list_filter = ('school',)


admin.site.register(CollectAdmFee, CollectAdmFeeAdmin)




