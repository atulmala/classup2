from django.contrib import admin

from academics.models import ThirdLang
from .models import Scheme

# Register your models here.


class ThirdLangAdmin(admin.ModelAdmin):
    list_display = ('student', 'third_lang',)


admin.site.register(ThirdLang, ThirdLangAdmin)


class SchemeAdmin(admin.ModelAdmin):
    list_display = ('school', 'the_class', 'sequence', 'subject',)


admin.site.register(Scheme, SchemeAdmin)
