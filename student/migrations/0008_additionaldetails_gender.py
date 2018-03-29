# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0007_house'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionaldetails',
            name='gender',
            field=models.CharField(default=b' ', max_length=6),
        ),
    ]
