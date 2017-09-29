# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0016_coscholastics_grade_term'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coscholastics',
            name='promoted_to_class',
            field=models.CharField(default=b' ', max_length=10),
        ),
        migrations.AlterField(
            model_name='coscholastics',
            name='teacher_remarks',
            field=models.CharField(default=b'All the Best', max_length=100),
        ),
    ]
