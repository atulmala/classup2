# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0022_auto_20180302_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='bulk_sms_delay',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='configurations',
            name='vendor_bulk_sms',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='configurations',
            name='vendor_sms',
            field=models.IntegerField(default=2),
        ),
    ]
