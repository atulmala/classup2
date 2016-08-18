# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
        ('teacher', '0001_initial'),
        ('academics', '0003_auto_20160817_1644'),
        ('setup', '0006_userschoolmapping'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('school', models.ForeignKey(to='setup.School')),
                ('section', models.ForeignKey(to='academics.Section')),
                ('student', models.ForeignKey(to='student.Student')),
                ('subject', models.ForeignKey(to='academics.Subject')),
                ('taken_by', models.ForeignKey(default=None, to='teacher.Teacher', null=True)),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
        migrations.CreateModel(
            name='AttendanceTaken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('school', models.ForeignKey(to='setup.School')),
                ('section', models.ForeignKey(to='academics.Section')),
                ('subject', models.ForeignKey(to='academics.Subject')),
                ('taken_by', models.ForeignKey(default=None, to='teacher.Teacher', null=True)),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
    ]
