# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0009_auto_20190207_1420'),
    ]

    operations = [
        migrations.AddField(
            model_name='marksheet',
            name='show_attendance',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='npromoted',
            name='details',
            field=models.CharField(default=b'  ', max_length=200),
        ),
    ]
