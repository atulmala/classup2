# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0010_auto_20161010_0051'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='status',
            field=models.CharField(default=b'Not Available', max_length=200),
        ),
        migrations.AddField(
            model_name='smsrecord',
            name='status_extracted',
            field=models.BooleanField(default=False),
        ),
    ]
