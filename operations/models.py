from datetime import datetime
from django.db import models

from django.contrib.auth.models import User
from setup.models import School
from teacher.models import Teacher

# Create your models here.


class SMSRecord(models.Model):
    school = models.ForeignKey(School, null=True)
    sender = models.ForeignKey(Teacher)
    date = models.DateField(default=datetime.now)
    recipient = models.ForeignKey(User)
    message = models.TextField()
    outcome = models.TextField(max_length=20, default='Delivered')
