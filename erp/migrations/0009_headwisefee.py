# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_auto_20180329_1858'),
        ('setup', '0023_auto_20180830_1504'),
        ('erp', '0008_feepaymenthistory_receipt_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeadWiseFee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(auto_now_add=True)),
                ('head', models.CharField(max_length=20)),
                ('amount', models.DecimalField(max_digits=7, decimal_places=2)),
                ('PaymentHistory', models.ForeignKey(to='erp.FeePaymentHistory')),
                ('school', models.ForeignKey(to='setup.School')),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
