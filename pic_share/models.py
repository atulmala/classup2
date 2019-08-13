from django.db import models

from teacher.models import Teacher
from academics.models import Class, Section
from student.models import Student

# Create your models here.


class ImageVideo(models.Model):
    teacher = models.ForeignKey(Teacher)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)
    creation_date = models.DateTimeField(null=True, auto_now_add=True)
    type = models.CharField(max_length=10, default='image')
    descrition = models.CharField(max_length=200)
    location = models.ImageField(upload_to='image_video/')
    active_status = models.BooleanField(default=True)


class ShareWithStudents(models.Model):
    image_video = models.ForeignKey(ImageVideo)
    student = models.ForeignKey(Student)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)



