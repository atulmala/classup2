from django.db import models

from setup.models import School
from academics.models import Class, Subject
from student.models import Student

# Create your models here.


class Scheme(models.Model):
    school = models.ForeignKey(School)
    the_class = models.ForeignKey(Class)
    sequence = models.IntegerField()
    subject = models.ForeignKey(Subject)
    subject_type = models.CharField(max_length=50, default='Regular')


class HigherClassMapping(models.Model):
    student = models.ForeignKey(Student)
    subject = models.ForeignKey(Subject)
