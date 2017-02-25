# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0002_auto_20160917_0914'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='active_status',
            field=models.BooleanField(default=True),
        ),
    ]
