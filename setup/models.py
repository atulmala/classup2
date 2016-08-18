from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User


class School(models.Model):
    school_name = models.CharField(max_length=200)
    school_address = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return str(self.id) + ', ' + str(self.school_name)


class Configurations(models.Model):
    school = models.ForeignKey(School)
    router_server_ip = models.CharField(max_length=50, default='0.0.0.0')
    school_group_id = models.CharField(max_length=10, default=None)
    send_absence_sms = models.BooleanField(default=True)
    send_period_bunk_sms = models.BooleanField(default=False)
    send_marks_sms = models.BooleanField(default=True)
    send_results_sms = models.BooleanField(default=True)
    send_test_scheduled_sms = models.BooleanField(default=False)
    send_bus_reached_to_school_sms = models.BooleanField(default=False)
    send_bus_started_from_school_sms = models.BooleanField(default=False)
    send_all_parent_sms_to_principal = models.BooleanField(default=False)
    session_start_month = models.IntegerField(default=4)
    principal_mobile = models.CharField(max_length=20, default='1234567890')
    admin1_mobile = models.CharField(max_length=20, default='1234567890')
    admin2_mobile = models.CharField(max_length=20, default='1234567890')
    admin3_mobile = models.CharField(max_length=20, default='1234567890')
    admin4_mobile = models.CharField(max_length=20, default='1234567890')
    transport_incharge_mobile = models.CharField(max_length=20, default='1234567890')
    absence_sms_prolog = models.CharField(max_length=200, default=' ', null=True)
    absence_sms_epilog = models.CharField(max_length=200, default=' ', null=True)
    marks_sms_prolog = models.CharField(max_length=200, default=' ', null=True)
    marks_sms_epilog = models.CharField(max_length=200, default=' ', null=True)
    results_sms_prolog = models.CharField(max_length=200, default=' ', null=True)
    results_sms_epilog = models.CharField(max_length=200, default=' ', null=True)
    bunk_sms_prolog = models.CharField(max_length=200, default=' ', null=True)
    bunk_sms_epilog = models.CharField(max_length=200, default=' ', null=True)
    teacher_sms_prolog = models.CharField(max_length=200, default=' ', null=True)
    teacher_sms_epilog = models.CharField(max_length=200, default=' ', null=True)
    google_play_link = models.CharField(max_length=100, default=' ', null=True)
    app_store_link = models.CharField(max_length=100, default=' ', null=True)

    def __unicode__(self):
        return str(self.school.id) + ', ' + self.school.school_name


class UserSchoolMapping(models.Model):
    user = models.ForeignKey(User)
    school = models.ForeignKey(School)

    def __unicode__(self):
        return self.user.username + ' ' + self.school.school_name

