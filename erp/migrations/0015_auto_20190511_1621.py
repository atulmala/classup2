# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0014_feepaymenthistory_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feepaymenthistory',
            name='data',
            field=models.CharField(max_length=300, null=True, blank=True),
        ),
    ]
