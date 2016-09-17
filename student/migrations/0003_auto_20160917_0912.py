# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0002_auto_20160819_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='student_erp_id',
            field=models.CharField(max_length=30, null=True, db_column=b'student_erp_id', blank=True),
        ),
    ]
