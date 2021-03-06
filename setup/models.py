from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User


class SchoolGroup(models.Model):
    group_name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.group_name


class School(models.Model):
    group = models.ForeignKey(SchoolGroup, null=True)
    school_name = models.CharField(max_length=200)
    school_address = models.CharField(max_length=200, blank=True)
    subscription_active = models.BooleanField(default=True)

    def __unicode__(self):
        return str(self.school_name)

    class Meta:
        ordering = ['school_name']


class GlobalConf(models.Model):
    server_url = models.CharField(max_length=100, default="https://www.classupclient.com/")
    aws_s3_bucket = models.CharField(max_length=20, default='classup2')
    aws_access_key = models.CharField(max_length=40, default='AKIAJ6X32EHNR26CXSWA')
    aws_secret_key = models.CharField(max_length=50, default='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')
    aws_region = models.CharField(max_length=20, default='us-east-1')
    short_link_api = models.CharField(max_length=100, default='4f79464452b3bbed98ae6b42d717ac399cbaa')


class Configurations(models.Model):
    school = models.ForeignKey(School)
    school_short_name = models.CharField(max_length=20, default='model')
    type = models.CharField(max_length=20, default='school')
    login_prefix = models.CharField(max_length=20, default='@classup.com')
    router_server_ip = models.CharField(max_length=50, default='0.0.0.0')
    school_group_id = models.CharField(max_length=10, default=None)
    sender_id = models.CharField(max_length=10, default='ClssUp')
    send_sms = models.BooleanField(default=True)
    enable_bus_attendance = models.BooleanField(default=False)
    send_absence_sms = models.BooleanField(default=True)
    send_absence_sms_both_to_parent = models.BooleanField(default=True)
    send_period_bunk_sms = models.BooleanField(default=False)
    send_marks_sms = models.BooleanField(default=True)
    include_max_avg_marks = models.BooleanField(default=True)
    include_welcome_sms = models.BooleanField(default=False)
    send_results_sms = models.BooleanField(default=True)
    send_test_scheduled_sms = models.BooleanField(default=False)
    send_bus_reached_to_school_sms = models.BooleanField(default=False)
    send_bus_started_from_school_sms = models.BooleanField(default=False)
    send_all_parent_sms_to_principal = models.BooleanField(default=False)
    session_start_month = models.IntegerField(default=4)
    vendor_sms = models.IntegerField(default=2)
    vendor_bulk_sms = models.IntegerField(default=1)
    bulk_sms_delay = models.IntegerField(default=5)
    principal_mobile = models.CharField(max_length=20, default='1234567890')
    admin1_mobile = models.CharField(max_length=20, default='1234567890') # Vice Principal
    admin2_mobile = models.CharField(max_length=20, default='1234567890')   # Accounts Department
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
    google_play_link = models.CharField(max_length=100,
                                        default='https://play.google.com/store/apps/details?id=com.classup', null=True)
    app_store_link = models.CharField(max_length=100,
                                      default='https://itunes.apple.com/us/app/classup/id1100776259?mt=8&uo=4',
                                      null=True)

    def __unicode__(self):
        return self.school.school_name

    class Meta:
        ordering = ('school__school_name', )


class UserSchoolMapping(models.Model):
    user = models.ForeignKey(User)
    school = models.ForeignKey(School)

    def __unicode__(self):
        return self.user.username + ' ' + self.school.school_name

    class Meta:
        ordering = ['user']

