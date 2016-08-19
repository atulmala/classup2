# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='student_erp_id',
            field=models.CharField(max_length=20, null=True, db_column=b'student_erp_id', blank=True),
        ),
    ]
