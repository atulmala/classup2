# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0004_auto_20190324_0850'),
    ]

    operations = [
        migrations.AddField(
            model_name='feepaymenthistory',
            name='discount',
            field=models.DecimalField(default=0.0, max_digits=7, decimal_places=2),
        ),
        migrations.AddField(
            model_name='feepaymenthistory',
            name='fine',
            field=models.DecimalField(default=0.0, max_digits=7, decimal_places=2),
        ),
    ]
