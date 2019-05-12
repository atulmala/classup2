# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0013_feepaymenthistory_one_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='feepaymenthistory',
            name='data',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
