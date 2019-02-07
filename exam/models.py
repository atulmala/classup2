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

    def __unicode__(self):
        return self.subject.subject_name


class NotPromoted(models.Model):
    student = models.ForeignKey(Student)


class NPromoted(models.Model):
    student = models.ForeignKey(Student)
    details = models.CharField(max_length=100, default='  ')


class Marksheet(models.Model):
    school = models.ForeignKey(School)
    title_start = models.IntegerField(default=120)
    address_start = models.IntegerField(default=145)
    place = models.CharField(max_length=150, default='Place')
    result_date = models.CharField(max_length=10, default='20/03/2019')

    def __unicode__(self):
        return self.school.school_name




