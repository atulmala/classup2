# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0003_previousbalance'),
    ]

    operations = [
        migrations.AddField(
            model_name='feepaymenthistory',
            name='bank',
            field=models.CharField(default=b'N/A', max_length=20),
        ),
        migrations.AddField(
            model_name='feepaymenthistory',
            name='cheque_number',
            field=models.CharField(default=b'N/A', max_length=6),
        ),
    ]
