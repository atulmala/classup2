from django.contrib import admin

# Register your models here.
from lectures.models import Lecture


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    def get_school_name(self, obj):
        return obj.teacher.school

    list_display = ('get_school_name', 'teacher', 'the_class', 'section', 'subject',
                    'topic', 'youtube_link', 'pdf_link')
    list_filter = ('teacher__school',)

