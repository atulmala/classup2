# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0019_collectadmfee_whether_paid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feepaymenthistory',
            name='date',
            field=models.DateField(),
        ),
    ]
