# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0008_teacherattendance'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherAttendnceTaken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('taken_time', models.DateTimeField(default=datetime.datetime.now, blank=True)),
            ],
        ),
    ]
