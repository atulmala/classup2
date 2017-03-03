# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0015_auto_20161225_1824'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='login_prefix',
            field=models.CharField(default=b'@classup.com', max_length=20),
        ),
    ]
