# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0002_smsrecord_school'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='outcome',
            field=models.TextField(default=b'Delivered', max_length=20),
        ),
    ]
