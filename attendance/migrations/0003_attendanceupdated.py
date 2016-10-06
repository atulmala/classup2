# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0002_auto_20160917_0914'),
        ('academics', '0006_remove_classtest_school'),
        ('attendance', '0002_auto_20160820_1419'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceUpdated',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('update_date_time', models.DateTimeField(default=datetime.datetime.now, blank=True)),
                ('section', models.ForeignKey(to='academics.Section')),
                ('subject', models.ForeignKey(to='academics.Subject')),
                ('the_class', models.ForeignKey(to='academics.Class')),
                ('updated_by', models.ForeignKey(default=None, to='teacher.Teacher', null=True)),
            ],
        ),
    ]
