# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_user_device_mapping'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user_device_mapping',
            name='token_id',
            field=models.CharField(max_length=500),
        ),
    ]
