from datetime import datetime

from django.db import models
from setup.models import School
from student.models import Student


# Create your models here.
class Teacher(models.Model):
    teacher_erp_id = models.CharField(max_length=30, default='NA')    # this can be the existing employee id of the teacher
    school = models.ForeignKey(School)
    first_name = models.CharField(max_length=50, blank=False, null=False)
    last_name = models.CharField(max_length=50, null=True, blank=True, default=' ')
    email = models.EmailField(default='defaultemail@classup.in')     # email will also be used as login id
    mobile = models.CharField(max_length=20, blank=False, null=True)
    active_status = models.BooleanField(default=True)

    class Meta:
        ordering = ('first_name', )

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name


class Staff(models.Model):
    staff_erp_id = models.CharField(max_length=30, default='NA')    # this can be the existing employee id of the teacher
    school = models.ForeignKey(School)
    first_name = models.CharField(max_length=50, blank=False, null=False)
    last_name = models.CharField(max_length=50, null=True, blank=True, default=' ')
    email = models.EmailField(default='defaultemail@classup.in')     # email will also be used as login id
    mobile = models.CharField(max_length=20, blank=False, null=True)
    active_status = models.BooleanField(default=True)

    class Meta:
        ordering = ('first_name', )

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name


class TeacherAttendance(models.Model):
    school = models.ForeignKey(School, null=True)
    date = models.DateField()
    teacher = models.ForeignKey(Teacher)

    def save(self, *args, **kwargs):
        school = self.teacher.school
        self.school = school
        super(TeacherAttendance, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%s %s %s' % (self.school.school_name, self.date.strftime('%Y-%m-%d'), self.teacher.first_name)


class TeacherAttendnceTaken (models.Model):
    school = models.ForeignKey(School, null=True)
    date = models.DateField()
    taken_time = models.DateTimeField(default=datetime.now, blank=True)


class TeacherMessageRecord (models.Model):
    date = models.DateTimeField(default=datetime.now)
    teacher = models.ForeignKey (Teacher)
    message = models.TextField()
    sent_to = models.CharField(max_length=20)
    the_class = models.CharField(max_length=30, null=True)
    section = models.CharField(max_length=30, null=True)
    activity_group = models.CharField(max_length=50, null=True)


class MessageReceivers (models.Model):
    date = models.DateTimeField(null=True)
    teacher_record = models.ForeignKey (TeacherMessageRecord)
    student = models.ForeignKey (Student)
    full_message = models.TextField()
    outcome = models.TextField(max_length=20, default='Awaited')
    status = models.CharField (max_length=100, null=True)
    status_extracted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.date = self.teacher_record.date
        super (MessageReceivers, self).save(*args, **kwargs)




