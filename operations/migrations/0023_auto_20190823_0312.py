# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0022_paranshabd_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsrecord',
            name='status',
            field=models.CharField(default=b'Not Available', max_length=350),
        ),
    ]
