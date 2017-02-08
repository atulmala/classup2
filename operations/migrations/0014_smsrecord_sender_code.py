# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0013_auto_20170207_2303'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='sender_code',
            field=models.CharField(default=b'ClssUp', max_length=20),
        ),
    ]
