# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0015_auto_20180204_1552'),
        ('setup', '0022_auto_20180302_1729'),
        ('academics', '0022_auto_20180319_2204'),
        ('time_table', '0006_period_symbol'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassTimeTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('day', models.ForeignKey(to='time_table.DaysOfWeek')),
                ('period', models.ForeignKey(to='time_table.Period')),
                ('school', models.ForeignKey(to='setup.School')),
                ('section', models.ForeignKey(to='academics.Section')),
                ('subject', models.ForeignKey(to='academics.Subject', null=True)),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
    ]
