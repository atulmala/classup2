from datetime import datetime

from django.db import models
from setup.models import School


# Create your models here.
class Teacher(models.Model):
    teacher_erp_id = models.CharField(max_length=30, default='NA')    # this can be the existing employee id of the teacher
    school = models.ForeignKey(School)
    first_name = models.CharField(max_length=50, blank=False, null=False)
    last_name = models.CharField(max_length=50, null=True, blank=True, default=' ')
    email = models.EmailField(default='defaultemail@classup.in')     # email will also be used as login id
    mobile = models.CharField(max_length=20, blank=False, null=True)
    active_status = models.BooleanField(default=True)

    def __unicode__(self):
        return self.first_name


class TeacherAttendance(models.Model):
    date = models.DateField()
    teacher = models.ForeignKey(Teacher)


class TeacherAttendnceTaken (models.Model):
    date = models.DateField()
    taken_time = models.DateTimeField(default=datetime.now, blank=True)


DAYS_OF_WEEK = (
    ('Mon', 'Mon'),
    ('Tue', 'Tue'),
    ('Wed', 'Wed'),
    ('Thu', 'Thu'),
    ('Fri', 'Fri'),
    ('Sat', 'Sat'),
    ('Sun', 'Sun'),
)


