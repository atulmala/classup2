# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0031_subject_grade_based'),
        ('online_test', '0002_onlinetest_school'),
    ]

    operations = [
        migrations.AddField(
            model_name='onlinetest',
            name='exam',
            field=models.ForeignKey(to='academics.Exam', null=True),
        ),
    ]
