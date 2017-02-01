from datetime import datetime
from django.db import models

from django.contrib.auth.models import User
from setup.models import School
from teacher.models import Teacher

# Create your models here.


class SMSRecord(models.Model):
    school = models.ForeignKey(School, null=True)
    sender = models.ForeignKey(Teacher, null=True)
    sender1 = models.CharField(max_length=100, default='Not Available')
    sender_type = models.CharField(max_length=20, default='Not Available')
    date = models.DateTimeField(default=datetime.now)
    recipient = models.ForeignKey(User, null=True)
    recipient_name = models.CharField(max_length=100, default='Not Available')
    recipient_number = models.CharField(max_length=20, default='Not Available')
    recipient_type = models.CharField(max_length=20, default='Not Available')
    message = models.TextField()
    message_type = models.CharField(max_length=30, default='Not Available')
    outcome = models.TextField(max_length=20, default='Delivered')
    status_extracted = models.BooleanField(default=False)
    status = models.CharField(max_length=200, default='Not Available')
