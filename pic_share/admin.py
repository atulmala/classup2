from django.contrib import admin

from .models import ImageVideo, ShareWithStudents, CredentialModel

# Register your models here.


class ImageVideoAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'the_class', 'section', 'type',
                    'creation_date', 'descrition', 'location', 'short_link',)
    search_fields = ('teacher',)
    list_filter = ('creation_date', 'teacher__school',)


admin.site.register(ImageVideo, ImageVideoAdmin)


class SharedAdmin(admin.ModelAdmin):
    list_display = ('image_video', 'student', 'the_class', 'section',)


admin.site.register(ShareWithStudents, SharedAdmin)


class CredentialAdmin(admin.ModelAdmin):
    list_display = ('credential',)


admin.site.register(CredentialModel, CredentialAdmin)



