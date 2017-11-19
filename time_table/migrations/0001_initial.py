# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0019_auto_20171031_2142'),
        ('teacher', '0010_auto_20171109_1116'),
        ('academics', '0020_subject_subject_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='DaysOfWeek',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('day', models.CharField(max_length=20)),
                ('sequence', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('period', models.CharField(max_length=10)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
        migrations.CreateModel(
            name='TimeTable',
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
        migrations.CreateModel(
            name='Wing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wing', models.CharField(max_length=20)),
                ('start_class', models.IntegerField()),
                ('end_class', models.IntegerField()),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
