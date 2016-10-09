# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0004_auto_20161009_1950'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='sender1',
            field=models.CharField(default=b'Not Available', max_length=100),
        ),
    ]
