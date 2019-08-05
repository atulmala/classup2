from django.contrib import admin

from .models import ImageVideo, ShareWithStudents

# Register your models here.


class ImageVideoAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'the_class', 'section', 'type',
                    'creation_date', 'descrition', 'location',)
    search_fields = ('teacher',)
    list_filter = ('creation_date',)


admin.site.register(ImageVideo, ImageVideoAdmin)


class SharedAdmin(admin.ModelAdmin):
    list_display = ('image_video', 'student', 'the_class', 'section',)


admin.site.register(ShareWithStudents, SharedAdmin)



