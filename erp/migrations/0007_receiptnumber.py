# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0023_auto_20180830_1504'),
        ('erp', '0006_feepaymenthistory_previous_due'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceiptNumber',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_receipt', models.IntegerField(default=1000, max_length=6)),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
