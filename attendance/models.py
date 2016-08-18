from django.db import models
from setup.models import School
from student.models import Student
from academics.models import Class, Section, Subject, Teacher

# Create your models here.


class Attendance(models.Model):
    school = models.ForeignKey(School)
    date = models.DateField()
    the_class = models.ForeignKey(Class)    # the name of field is the_class because class may be reserved word
    section = models.ForeignKey(Section)
    subject = models.ForeignKey(Subject)
    student = models.ForeignKey(Student)
    taken_by = models.ForeignKey(Teacher, default=None, null=True)


class AttendanceTaken(models.Model):
    school = models.ForeignKey(School)
    date = models.DateField()
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)
    subject = models.ForeignKey(Subject)
    taken_by = models.ForeignKey(Teacher, default=None, null=True)

