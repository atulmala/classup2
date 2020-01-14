# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0012_auto_20191117_0304'),
        ('erp', '0020_auto_20190704_1703'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectTransportFee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bus_fee', models.DecimalField(max_digits=8, decimal_places=2)),
                ('slab', models.CharField(max_length=2)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
