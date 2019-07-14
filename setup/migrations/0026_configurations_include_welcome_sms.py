# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0025_auto_20190408_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='include_welcome_sms',
            field=models.BooleanField(default=False),
        ),
    ]
