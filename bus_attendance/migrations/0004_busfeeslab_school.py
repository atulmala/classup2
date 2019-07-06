# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0025_auto_20190408_1422'),
        ('bus_attendance', '0003_auto_20190706_0203'),
    ]

    operations = [
        migrations.AddField(
            model_name='busfeeslab',
            name='school',
            field=models.ForeignKey(to='setup.School', null=True),
        ),
    ]
