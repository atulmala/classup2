# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0012_configurations_include_max_avg_marks'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='send_sms',
            field=models.BigIntegerField(default=True),
        ),
    ]
