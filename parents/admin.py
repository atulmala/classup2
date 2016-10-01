from django.contrib import admin

from .models import ParentCommunicationCategories, ParentCommunication

# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(ParentCommunicationCategories, CategoryAdmin)


class ParentCommunicationsAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.student.school
    get_school_name.short_description = 'School'

    def get_parent_name(self, obj):
        return obj.student.parent
    get_parent_name.short_description = 'Parent'

    list_display = ('get_school_name', 'get_parent_name',
                    'student', 'date_sent', 'category', 'communication_text',)
    list_filter = ('date_sent', 'category',)

admin.site.register(ParentCommunication, ParentCommunicationsAdmin)
