from django.contrib import admin
from student.models import AdditionalDetails

# Register your models here.


class AdditionalDetailsAdmin(admin.ModelAdmin):
    list_display = ('student', 'mother_name', 'address',)
    search_fields = ('student__fist_name', 'student__last_name')
    list_filter = ('student__school',)

admin.site.register(AdditionalDetails, AdditionalDetailsAdmin)

