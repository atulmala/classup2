# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0013_configurations_send_sms'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='sender_id',
            field=models.CharField(default=b'ClssUp', max_length=10),
        ),
    ]
