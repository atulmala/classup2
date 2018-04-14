# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0022_auto_20180302_1729'),
        ('academics', '0022_auto_20180319_2204'),
    ]

    operations = [
        migrations.CreateModel(
            name='Exam1',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('start_class', models.CharField(max_length=20, null=True)),
                ('start_class_sequence', models.SmallIntegerField(null=True)),
                ('end_class', models.CharField(max_length=20, null=True)),
                ('end_class_sequence', models.SmallIntegerField(null=True)),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
