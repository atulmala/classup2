# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0011_auto_20170723_0003'),
    ]

    operations = [
        migrations.AddField(
            model_name='user_device_mapping',
            name='player_id',
            field=models.CharField(default=b'Unavailable', max_length=40),
        ),
    ]
