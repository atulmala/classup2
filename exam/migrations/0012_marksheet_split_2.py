# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0011_marksheet_theory_prac_split'),
    ]

    operations = [
        migrations.AddField(
            model_name='marksheet',
            name='split_2',
            field=models.CharField(default=b' ', max_length=b'200'),
        ),
    ]
