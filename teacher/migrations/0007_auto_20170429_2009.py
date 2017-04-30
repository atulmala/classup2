# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0006_auto_20170303_1443'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='last_name',
            field=models.CharField(default=b' ', max_length=50, null=True, blank=True),
        ),
    ]
