from django.db import models

from setup.models import School
from student.models import Student
from teacher.models import Teacher

# Create your models here.


class ActivityGroup(models.Model):
    school = models.ForeignKey(School)
    group_name = models.CharField(max_length=100)
    group_description = models.CharField(max_length=100, default='Activity Group')
    group_incharge = models.ForeignKey(Teacher)


class ActivityMembers(models.Model):
    student = models.ForeignKey(Student)
