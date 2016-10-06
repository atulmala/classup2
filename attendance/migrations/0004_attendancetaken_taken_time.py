# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_attendanceupdated'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancetaken',
            name='taken_time',
            field=models.DateTimeField(default=datetime.datetime.now, blank=True),
        ),
    ]
