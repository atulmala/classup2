from django.db import models

# Create your models here.


class SMSDelStats(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    time_taken = models.IntegerField()
    messages_count = models.IntegerField()
