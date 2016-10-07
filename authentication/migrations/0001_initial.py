# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LoginRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_and_time', models.DateTimeField(default=datetime.datetime.now, blank=True)),
                ('login_id', models.CharField(max_length=100)),
                ('password', models.CharField(max_length=100)),
                ('ip_address', models.IPAddressField(blank=True)),
                ('city', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('result', models.CharField(max_length=20)),
                ('comments', models.CharField(max_length=200)),
            ],
        ),
    ]
