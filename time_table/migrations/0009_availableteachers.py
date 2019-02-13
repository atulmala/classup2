# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0015_auto_20180204_1552'),
        ('setup', '0023_auto_20180830_1504'),
        ('time_table', '0008_ctimetable'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailableTeachers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('day', models.ForeignKey(to='time_table.DaysOfWeek')),
                ('period', models.ForeignKey(to='time_table.Period')),
                ('school', models.ForeignKey(to='setup.School')),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
            ],
        ),
    ]
