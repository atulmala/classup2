# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0010_auto_20190505_1418'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionaldetails',
            name='blood_group',
            field=models.CharField(default=b'NA', max_length=10),
        ),
    ]
