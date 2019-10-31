# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0005_studenttotalmarks_rank'),
    ]

    operations = [
        migrations.AddField(
            model_name='studenttotalmarks',
            name='out_of',
            field=models.IntegerField(default=0),
        ),
    ]
