# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0010_auto_20190310_0325'),
    ]

    operations = [
        migrations.AddField(
            model_name='marksheet',
            name='theory_prac_split',
            field=models.CharField(default=b' ', max_length=b'200'),
        ),
    ]
