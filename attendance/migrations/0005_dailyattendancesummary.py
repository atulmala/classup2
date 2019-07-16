# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0029_auto_20190220_1423'),
        ('attendance', '0004_attendancetaken_taken_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyAttendanceSummary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('total', models.IntegerField()),
                ('present', models.IntegerField()),
                ('absent', models.IntegerField()),
                ('percentage', models.DecimalField(max_digits=6, decimal_places=2)),
                ('section', models.ForeignKey(to='academics.Section')),
                ('subject', models.ForeignKey(to='academics.Subject')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
    ]
