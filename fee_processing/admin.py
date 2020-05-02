from django.contrib import admin

# Register your models here.
from fee_processing.models import FeeDefaulters


@admin.register(FeeDefaulters)
class FeeDefaultersAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount_due',)
