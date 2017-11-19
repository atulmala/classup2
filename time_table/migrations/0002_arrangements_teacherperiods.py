# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0019_auto_20171031_2142'),
        ('teacher', '0010_auto_20171109_1116'),
        ('academics', '0020_subject_subject_type'),
        ('time_table', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Arrangements',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('period', models.ForeignKey(to='time_table.Period')),
                ('school', models.ForeignKey(to='setup.School')),
                ('section', models.ForeignKey(to='academics.Section')),
                ('subject', models.ForeignKey(to='academics.Subject', null=True)),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
        migrations.CreateModel(
            name='TeacherPeriods',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('day', models.ForeignKey(to='time_table.DaysOfWeek')),
                ('period', models.ForeignKey(to='time_table.Period')),
                ('school', models.ForeignKey(to='setup.School')),
                ('section', models.ForeignKey(to='academics.Section')),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
    ]
