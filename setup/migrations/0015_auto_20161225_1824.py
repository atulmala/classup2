# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0014_configurations_sender_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configurations',
            name='send_sms',
            field=models.BooleanField(default=True),
        ),
    ]
