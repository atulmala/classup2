# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_auto_20161007_1032'),
    ]

    operations = [
        migrations.AddField(
            model_name='loginrecord',
            name='login_type',
            field=models.CharField(default=b'Device', max_length=10),
        ),
    ]
