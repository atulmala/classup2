# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fee_processing', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedefaulters',
            name='stop_access',
            field=models.BooleanField(default=False),
        ),
    ]
