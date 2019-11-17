# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0011_auto_20190530_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionaldetails',
            name='blood_group',
            field=models.CharField(default=b'NA', max_length=20),
        ),
    ]
