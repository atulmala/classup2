# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0020_auto_20180204_1552'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalconf',
            name='aws_region',
            field=models.CharField(default=b'us-east-1', max_length=20),
        ),
    ]
