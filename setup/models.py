from django.db import models

# Create your models here.

from django.db import models


class School(models.Model):
    school_id = models.CharField(max_length=10, unique=True)
    school_name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.school_id


class Configurations(models.Model):
    school = models.ForeignKey(School)
    router_server_ip = models.CharField(max_length=50)
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
    absence_sms_prolog = models.CharField(max_length=200, default=None, null=True)
    absence_sms_epilog = models.CharField(max_length=200, default=None, null=True)
    marks_sms_prolog = models.CharField(max_length=200, default=None, null=True)
    marks_sms_epilog = models.CharField(max_length=200, default=None, null=True)
    results_sms_prolog = models.CharField(max_length=200, default=None, null=True)
    results_sms_epilog = models.CharField(max_length=200, default=None, null=True)
    bunk_sms_prolog = models.CharField(max_length=200, default=None, null=True)
    bunk_sms_epilog = models.CharField(max_length=200, default=None, null=True)
    teacher_sms_prolog = models.CharField(max_length=200, default=None, null=True)
    teacher_sms_epilog = models.CharField(max_length=200, default=None, null=True)
    google_play_link = models.CharField(max_length=100, default=None, null=True)
    app_store_link = models.CharField(max_length=100, default=None, null=True)

    def __unicode__(self):
        return str(self.id)+ ' ' + self.school_name

