# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0011_auto_20190530_1657'),
        ('exam', '0012_marksheet_split_2'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stream',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stream', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='StreamMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stream', models.ForeignKey(to='exam.Stream')),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
