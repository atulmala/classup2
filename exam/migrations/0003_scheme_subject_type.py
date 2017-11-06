# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0002_auto_20171102_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='subject_type',
            field=models.CharField(default=b'Regular', max_length=50),
        ),
    ]
