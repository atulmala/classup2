# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0012_smsrecord_api_called'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsrecord',
            name='api_called',
            field=models.BooleanField(default=True),
        ),
    ]
