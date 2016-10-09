# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0008_auto_20161009_2233'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='recipient_number',
            field=models.CharField(default=b'Not Available', max_length=20),
        ),
    ]
