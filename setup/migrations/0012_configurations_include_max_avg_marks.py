# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0011_auto_20161006_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='include_max_avg_marks',
            field=models.BooleanField(default=True),
        ),
    ]
