# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0005_auto_20170301_1640'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='teacher_erp_id',
            field=models.CharField(default=b'NA', max_length=30),
        ),
    ]
