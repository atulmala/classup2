# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0008_auto_20160822_0352'),
        ('bus_attendance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bus_rout',
            name='school',
            field=models.ForeignKey(to='setup.School', null=True),
        ),
    ]
