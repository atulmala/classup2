# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
        ('teacher', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attedance_Type',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('route_type', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Bus_Attendance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('attendance_type', models.ForeignKey(to='bus_attendance.Attedance_Type')),
            ],
        ),
        migrations.CreateModel(
            name='Bus_Rout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bus_root', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='BusAttendanceTaken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('rout', models.ForeignKey(to='bus_attendance.Bus_Rout')),
                ('taken_by', models.ForeignKey(default=None, to='teacher.Teacher', null=True)),
                ('type', models.ForeignKey(to='bus_attendance.Attedance_Type')),
            ],
        ),
        migrations.CreateModel(
            name='BusStop',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stop_name', models.CharField(max_length=100)),
                ('bus_rout', models.ForeignKey(to='bus_attendance.Bus_Rout')),
            ],
        ),
        migrations.CreateModel(
            name='Student_Rout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bus_root', models.ForeignKey(to='bus_attendance.Bus_Rout')),
                ('bus_stop', models.ForeignKey(blank=True, to='bus_attendance.BusStop', null=True)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
        migrations.AddField(
            model_name='bus_attendance',
            name='bus_rout',
            field=models.ForeignKey(to='bus_attendance.Bus_Rout'),
        ),
        migrations.AddField(
            model_name='bus_attendance',
            name='student',
            field=models.ForeignKey(to='student.Student'),
        ),
        migrations.AddField(
            model_name='bus_attendance',
            name='taken_by',
            field=models.ForeignKey(default=None, to='teacher.Teacher', null=True),
        ),
    ]
