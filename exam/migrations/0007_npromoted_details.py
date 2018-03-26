# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0006_npromoted'),
    ]

    operations = [
        migrations.AddField(
            model_name='npromoted',
            name='details',
            field=models.CharField(default=b'  ', max_length=100),
        ),
    ]
