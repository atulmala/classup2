from django.db import models

from setup.models import School

# Create your models here.


class SMSDelStats(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    time_taken = models.IntegerField()
    messages_count = models.IntegerField()


class DailyMessageCount(models.Model):
    date = models.DateField()
    school = models.ForeignKey(School)
    message_count = models.IntegerField()
    sms_count = models.IntegerField()
