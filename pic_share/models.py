from django.db import models

from teacher.models import Teacher, Staff
from academics.models import Class, Section
from student.models import Student

# Create your models here.


class ImageVideo(models.Model):
    teacher = models.ForeignKey(Teacher, null=True)
    the_class = models.ForeignKey(Class, null=True)
    section = models.ForeignKey(Section, null=True)
    creation_date = models.DateTimeField(null=True, auto_now_add=True)
    type = models.CharField(max_length=10, default='image')
    descrition = models.CharField(max_length=200)
    location = models.ImageField(upload_to='image_video/')
    short_link = models.CharField(max_length=100, null=True)
    active_status = models.BooleanField(default=True)


class ShareWithStudents(models.Model):
    image_video = models.ForeignKey(ImageVideo)
    student = models.ForeignKey(Student)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)


class SharedWithTeacher(models.Model):
    image_video = models.ForeignKey(ImageVideo)
    teacher = models.ForeignKey(Teacher, null=True)
    staff = models.ForeignKey(Staff, null=True)



