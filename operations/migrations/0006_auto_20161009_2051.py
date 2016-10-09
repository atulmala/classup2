# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0005_smsrecord_sender1'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsrecord',
            name='date',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
