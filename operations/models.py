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
    status = models.CharField(max_length=250, default='Not Available')
    the_vendor = models.ForeignKey(SMSVendor, null=True, blank=True)


class ClassUpAdmin(models.Model):
    admin_mobile = models.CharField(max_length=20, default='9873011186')



