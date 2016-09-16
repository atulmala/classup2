from datetime import datetime
from django.db import models

from django.contrib.auth.models import User
from teacher.models import Teacher

# Create your models here.


class SMSRecord(models.Model):
    sender = models.ForeignKey(Teacher)
    date = models.DateField(default=datetime.now)
    recipient = models.ForeignKey(User)
    message = models.TextField()
