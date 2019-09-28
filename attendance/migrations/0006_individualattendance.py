# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0011_auto_20190530_1657'),
        ('attendance', '0005_dailyattendancesummary'),
    ]

    operations = [
        migrations.CreateModel(
            name='IndividualAttendance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('total_days', models.IntegerField()),
                ('present_days', models.IntegerField()),
                ('absent_days', models.IntegerField()),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
