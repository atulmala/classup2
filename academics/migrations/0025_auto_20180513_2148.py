# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0024_classtest_exam'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='exam_type',
            field=models.CharField(default=b'unit', max_length=20),
        ),
        migrations.AddField(
            model_name='exam1',
            name='exam_type',
            field=models.CharField(default=b'unit', max_length=20),
        ),
    ]
