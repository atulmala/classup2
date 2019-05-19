# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0025_auto_20190408_1422'),
        ('erp', '0016_auto_20190512_1239'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeeCorrection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(auto_now_add=True)),
                ('receipt_number', models.IntegerField()),
                ('amount', models.DecimalField(default=0.0, max_digits=7, decimal_places=2)),
                ('fine', models.DecimalField(default=0.0, max_digits=7, decimal_places=2)),
                ('one_time', models.DecimalField(default=0.0, max_digits=7, decimal_places=2)),
                ('discount', models.DecimalField(default=0.0, max_digits=7, decimal_places=2)),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
