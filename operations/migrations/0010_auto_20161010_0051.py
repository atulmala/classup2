# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0009_smsrecord_recipient_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsrecord',
            name='message_type',
            field=models.CharField(default=b'Not Available', max_length=30),
        ),
    ]
