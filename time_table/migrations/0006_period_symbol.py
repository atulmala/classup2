# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('time_table', '0005_classwingmapping_teacherwingmapping'),
    ]

    operations = [
        migrations.AddField(
            model_name='period',
            name='symbol',
            field=models.CharField(max_length=6, null=True),
        ),
    ]
