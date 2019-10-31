# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0006_studenttotalmarks_out_of'),
    ]

    operations = [
        migrations.AddField(
            model_name='studenttotalmarks',
            name='percentage',
            field=models.DecimalField(default=0.0, max_digits=6, decimal_places=2),
        ),
    ]
