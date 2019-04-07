# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0012_feepaymenthistory_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='feepaymenthistory',
            name='one_time',
            field=models.DecimalField(default=0.0, max_digits=7, decimal_places=2),
        ),
    ]
