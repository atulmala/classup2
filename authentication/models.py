from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from setup.models import School


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
    # 10/07/2017 - for getting the make & model, os version, screen resolution and size of the device
    model = models.CharField(max_length=200, default="Not available")
    os = models.CharField(max_length=200, default="Not available")
    resolution = models.CharField(max_length=100, default='Not available')
    size = models.CharField(max_length=100, default='Not available')


class LastPasswordReset(models.Model):
    login_id = models.CharField(max_length=100)
    last_reset_time = models.DateTimeField()


class user_device_mapping(models.Model):
    user = models.ForeignKey(User)
    mobile_number = models.CharField(max_length=20)
    token_id = models.CharField(max_length=500)
    device_type = models.CharField(max_length=20)


# 22/07/2017 - start logging important events & actions performed by users
class log_book(models.Model):
    date_and_time = models.DateTimeField(default=datetime.now)
    user = models.ForeignKey(User)
    user_name = models.CharField(max_length=100)
    school = models.ForeignKey(School)

