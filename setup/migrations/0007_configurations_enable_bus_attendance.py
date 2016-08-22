# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0006_userschoolmapping'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='enable_bus_attendance',
            field=models.BooleanField(default=False),
        ),
    ]
