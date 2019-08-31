# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0023_auto_20190823_0312'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='sms_consumed',
            field=models.IntegerField(default=0),
        ),
    ]
