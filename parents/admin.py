from django.contrib import admin

from .models import ParentCommunicationCategories, ParentCommunication

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(ParentCommunicationCategories, CategoryAdmin)


class ParentCommunicationsAdmin(admin.ModelAdmin):
    pass

admin.site.register(ParentCommunication, ParentCommunicationsAdmin)
