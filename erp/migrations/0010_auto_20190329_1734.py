# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_auto_20180329_1858'),
        ('erp', '0009_headwisefee'),
    ]

    operations = [
        migrations.AddField(
            model_name='previousbalance',
            name='parent',
            field=models.ForeignKey(to='student.Parent', null=True),
        ),
        migrations.AlterField(
            model_name='receiptnumber',
            name='start_receipt',
            field=models.IntegerField(default=1000),
        ),
    ]
