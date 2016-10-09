# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0006_auto_20161009_2051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsrecord',
            name='sender',
            field=models.ForeignKey(to='teacher.Teacher', null=True),
        ),
    ]
