from django.db import models

from setup.models import School
from teacher.models import Teacher
from academics.models import Class, Section, Subject

# Create your models here.


class Wing(models.Model):
    school = models.ForeignKey(School)
    wing = models.CharField(max_length=20)
    start_class = models.IntegerField()
    end_class = models.IntegerField()

    def __unicode__(self):
        return self.wing


class TeacherWingMapping (models.Model):
    school = models.ForeignKey(School)
    teacher = models.ForeignKey(Teacher)
    wing = models.ForeignKey(Wing)


class ClassWingMapping (models.Model):
    school = models.ForeignKey(School)
    the_class = models.ForeignKey(Class)
    wing = models.ForeignKey(Wing)

    def __unicode__(self):
        return self.school.school_name + ' ' + self.the_class.standard + ' ' + self.wing.wing


class DaysOfWeek(models.Model):
    day = models.CharField(max_length=20)
    sequence = models.IntegerField()

    def __unicode__(self):
        return self.day


class Period(models.Model):
    school = models.ForeignKey(School)
    period = models.CharField(max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()
    symbol = models.CharField(max_length=6, null=True)

    def __unicode__(self):
        return self.period


class TimeTable(models.Model):
    school = models.ForeignKey(School)
    day = models.ForeignKey(DaysOfWeek)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)
    period = models.ForeignKey(Period)
    subject = models.ForeignKey(Subject, null=True)
    teacher = models.ForeignKey(Teacher)


class TeacherPeriods (models.Model):
    school = models.ForeignKey(School)
    teacher = models.ForeignKey(Teacher)
    day = models.ForeignKey(DaysOfWeek)
    period = models.ForeignKey(Period)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)

    def __unicode__(self):
        return self.teacher.first_name + ' ' + self.teacher.last_name + ' ' + self.day.day + ' ' + \
               self.period.period + ' ' + self.the_class.standard + '-' + self.section.section


class Arrangements (models.Model):
    school = models.ForeignKey(School)
    date = models.DateField()
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)
    period = models.ForeignKey(Period)
    subject = models.ForeignKey(Subject, null=True)
    teacher = models.ForeignKey(Teacher)


class ExcludedFromArrangements (models.Model):
    school = models.ForeignKey(School)
    teacher = models.ForeignKey(TeacherPeriods)


class ExcludedFromArrangements1 (models.Model):
    school = models.ForeignKey(School)
    teacher = models.ForeignKey(Teacher)
