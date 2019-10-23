# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0015_auto_20191023_0510'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='max_marks',
            field=models.DecimalField(default=80.0, max_digits=6, decimal_places=2),
        ),
    ]
