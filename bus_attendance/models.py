from django.db import models

from student.models import Student
from teacher.models import Teacher

# Create your models here.


class Bus_Rout(models.Model):
    bus_root = models.CharField(max_length=50)

    def __unicode__(self):
        return self.bus_root


class BusStop(models.Model):
    stop_name = models.CharField(max_length=100)
    bus_rout = models.ForeignKey(Bus_Rout)

    def __unicode__(self):
        return self.stop_name + ' / ' + self.bus_rout.bus_root


class Student_Rout(models.Model):
    bus_root = models.ForeignKey(Bus_Rout)
    bus_stop = models.ForeignKey(BusStop, null=True, blank=True)
    student = models.ForeignKey(Student)


class Attedance_Type(models.Model):
    route_type = models.CharField(max_length=50)

    def __unicode__(self):
        return self.route_type


class Bus_Attendance(models.Model):
    date = models.DateField()
    bus_rout = models.ForeignKey(Bus_Rout)
    student = models.ForeignKey(Student)
    attendance_type = models.ForeignKey(Attedance_Type)
    taken_by = models.ForeignKey(Teacher, default=None, null=True)


class BusAttendanceTaken(models.Model):
    date = models.DateField()
    rout = models.ForeignKey(Bus_Rout)
    type = models.ForeignKey(Attedance_Type)
    taken_by = models.ForeignKey(Teacher, default=None, null=True)

    def __unicode__(self):
        return self.rout.bus_root + ' ' + self.type.route_type + ' ' + str(self.date)

