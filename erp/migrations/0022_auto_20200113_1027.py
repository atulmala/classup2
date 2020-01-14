# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0021_collecttransportfee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collecttransportfee',
            name='bus_fee',
            field=models.DecimalField(default=0.0, max_digits=8, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='collecttransportfee',
            name='slab',
            field=models.CharField(default=b'X', max_length=2),
        ),
    ]
