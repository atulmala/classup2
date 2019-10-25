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
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=80.00)
    subject_type = models.CharField(max_length=50, default='Regular')


class HigherClassMapping(models.Model):
    student = models.ForeignKey(Student)
    subject = models.ForeignKey(Subject)

    def __unicode__(self):
        return self.subject.subject_name


class Stream(models.Model):
    stream = models.CharField(max_length=100)

    def __unicode__(self):
        return self.stream


class StreamMapping(models.Model):
    student = models.ForeignKey(Student)
    stream = models.ForeignKey(Stream)


class NotPromoted(models.Model):
    student = models.ForeignKey(Student)


class NPromoted(models.Model):
    student = models.ForeignKey(Student)
    details = models.CharField(max_length=200, default='  ')


class Marksheet(models.Model):
    school = models.ForeignKey(School)
    title_start = models.IntegerField(default=120)
    address_start = models.IntegerField(default=145)
    place = models.CharField(max_length=150, default='Place')
    result_date = models.CharField(max_length=10, default='20/03/2019')
    show_attendance = models.BooleanField(default=False)
    theory_prac_split = models.CharField(max_length='200', default=' ')
    split_2 = models.CharField(max_length='200', default=' ')
    logo_left_margin = models.IntegerField(default=410)
    logo_width = models.IntegerField(default=65)
    affiliation = models.CharField(max_length=200, default='Affiliated to CBSE')
    board_logo_path = models.CharField(max_length=100,
                                       default='classup2/media/dev/cbse_logo/Logo/cbse-logo.png')


    def __unicode__(self):
        return self.school.school_name


class Wing(models.Model):
    school = models.ForeignKey(School, related_name='school')
    wing = models.CharField(max_length=50)
    classes = models.CharField(max_length=100)




