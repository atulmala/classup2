import math

from datetime import datetime
from django.db import models

from django.contrib.auth.models import User
from setup.models import School
from teacher.models import Teacher


# Create your models here.


class SMSVendor(models.Model):
    vendor = models.CharField(max_length=25, default='SoftSMS')

    def __unicode__(self):
        return self.vendor


class SMSRecord(models.Model):
    school = models.ForeignKey(School, null=True)
    sender = models.ForeignKey(Teacher, null=True)
    sender1 = models.CharField(max_length=100, default='Not Available')
    sender_type = models.CharField(max_length=20, default='Not Available')
    sender_code = models.CharField(max_length=20, default='ClssUp')
    date = models.DateTimeField(default=datetime.now)
    recipient = models.ForeignKey(User, null=True)
    recipient_name = models.CharField(max_length=100, default='Not Available')
    recipient_number = models.CharField(max_length=20, default='Not Available')
    recipient_type = models.CharField(max_length=20, default='Not Available')
    message = models.TextField()
    message_type = models.CharField(max_length=30, default='Not Available')
    vendor = models.CharField(max_length=30, default='1')
    api_called = models.BooleanField(default=True)
    outcome = models.TextField(max_length=20, default='Delivered')
    status_extracted = models.BooleanField(default=False)
    status = models.CharField(max_length=350, default='Not Available')
    the_vendor = models.ForeignKey(SMSVendor, null=True, blank=True)
    sms_consumed = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        try:
            self.sms_consumed = math.ceil(float(len(self.message)) / 160.0)
            print('%i sms credits consumed by this sms' % self.sms_consumed)
            super(SMSRecord, self).save(*args, **kwargs)
        except Exception as e:
            print('exception 31082019-A from operations models.py %s %s' % (e.message, type(e)))
            print('failed to determine the sms credits consumed by this sms')


class SMSBatch(models.Model):
    batch = models.CharField(max_length=20)
    total = models.IntegerField()
    success = models.IntegerField()
    fail = models.IntegerField()


class ResendSMS(models.Model):
    sms_record = models.ForeignKey(SMSRecord)
    outcome = models.TextField(max_length=30, default='Not Available')
    status = models.CharField(max_length=350, default='Not Available')


class ClassUpAdmin(models.Model):
    admin_mobile = models.CharField(max_length=20, default='9873011186')


class ParanShabd(models.Model):
    upbhokta = models.CharField(max_length=15)
    name = models.CharField(max_length=50, null=True)
    shabd = models.CharField(max_length=10)
