from datetime import datetime

from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class LoginRecord(models.Model):
    date_and_time = models.DateTimeField(default=datetime.now, blank=True)
    login_id = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    string_ip = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True)
    login_type = models.CharField(max_length=10, default='Device')
    outcome = models.CharField(max_length=10, default='Failed')
    comments = models.CharField(max_length=200)


class LastPasswordReset(models.Model):
    login_id = models.CharField(max_length=100)
    last_reset_time = models.DateTimeField()


class user_device_mapping(models.Model):
    user = models.ForeignKey(User)
    mobile_number = models.CharField(max_length=20)
    token_id = models.CharField(max_length=200)
    device_type = models.CharField(max_length=20)
