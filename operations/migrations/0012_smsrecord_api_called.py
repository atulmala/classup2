# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0011_auto_20170201_1921'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='api_called',
            field=models.BooleanField(default=False),
        ),
    ]
