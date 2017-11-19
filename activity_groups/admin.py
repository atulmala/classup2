from django.contrib import admin

from .models import *

# Register your models here.


class ActivityGroupAdmin (admin.ModelAdmin):
    list_display = ('school', 'group_name', 'group_incharge',)


admin.site.register(ActivityGroup, ActivityGroupAdmin)


class ActivityMembersAdmin (admin.ModelAdmin):
    list_display = ('group', 'student',)


admin.site.register(ActivityMembers, ActivityMembersAdmin)
