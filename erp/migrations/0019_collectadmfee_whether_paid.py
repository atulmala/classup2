# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0018_feepaymenthistory_waiver'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectadmfee',
            name='whether_paid',
            field=models.BooleanField(default=False),
        ),
    ]
