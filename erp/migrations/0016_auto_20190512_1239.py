# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0015_auto_20190511_1621'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feepaymenthistory',
            name='data',
            field=models.TextField(null=True, blank=True),
        ),
    ]
