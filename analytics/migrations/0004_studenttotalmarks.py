# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0030_termtestresult_multi_asses_marks'),
        ('student', '0011_auto_20190530_1657'),
        ('analytics', '0003_auto_20191027_1127'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentTotalMarks',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('total_marks', models.DecimalField(max_digits=6, decimal_places=2)),
                ('exam', models.ForeignKey(to='academics.Exam')),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
