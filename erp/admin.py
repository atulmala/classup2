from django.contrib import admin
from student.models import AdditionalDetails

# Register your models here.


class AdditionalDetailsAdmin(admin.ModelAdmin):
    list_display = ('student', 'mother_name', 'address',)

admin.site.register(AdditionalDetails, AdditionalDetailsAdmin)

