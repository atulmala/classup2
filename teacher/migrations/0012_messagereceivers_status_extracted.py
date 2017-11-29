# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0011_auto_20171129_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagereceivers',
            name='status_extracted',
            field=models.BooleanField(default=False),
        ),
    ]
