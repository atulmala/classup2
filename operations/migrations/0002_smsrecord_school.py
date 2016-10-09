# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0011_auto_20161006_1934'),
        ('operations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='school',
            field=models.ForeignKey(to='setup.School', null=True),
        ),
    ]
