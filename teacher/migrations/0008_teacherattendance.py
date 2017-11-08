# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0007_auto_20170429_2009'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherAttendance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
            ],
        ),
    ]
