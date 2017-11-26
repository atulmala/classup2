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

    def __unicode__(self):
        return self.group_name


class ActivityMembers(models.Model):
    group = models.ForeignKey(ActivityGroup, null=True)
    student = models.ForeignKey(Student)

