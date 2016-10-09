# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0003_smsrecord_outcome'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='message_type',
            field=models.CharField(default=b'Not Available', max_length=20),
        ),
        migrations.AddField(
            model_name='smsrecord',
            name='recipient_name',
            field=models.CharField(default=b'Not Available', max_length=100),
        ),
        migrations.AddField(
            model_name='smsrecord',
            name='recipient_type',
            field=models.CharField(default=b'Not Available', max_length=20),
        ),
        migrations.AddField(
            model_name='smsrecord',
            name='sender_type',
            field=models.CharField(default=b'Not Available', max_length=20),
        ),
    ]
