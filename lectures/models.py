from django.db import models

# Create your models here.
from academics.models import Class, Section, Subject
from teacher.models import Teacher


class Lecture(models.Model):
    teacher = models.ForeignKey(Teacher)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section, null=True)
    subject = models.ForeignKey(Subject)
    topic = models.CharField(max_length=100)
    youtube_link = models.CharField(max_length=200, null=True)
    pdf_link = models.CharField(max_length=200, null=True)

