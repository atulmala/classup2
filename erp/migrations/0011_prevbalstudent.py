# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_auto_20180329_1858'),
        ('setup', '0023_auto_20180830_1504'),
        ('erp', '0010_auto_20190329_1734'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrevBalStudent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('due_amount', models.DecimalField(default=0.0, max_digits=7, decimal_places=2)),
                ('negative', models.BooleanField(default=True)),
                ('parent', models.ForeignKey(to='student.Parent', null=True)),
                ('school', models.ForeignKey(to='setup.School')),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
