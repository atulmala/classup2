# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bus_attendance', '0002_bus_rout_school'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusFeeSlab',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slab', models.CharField(max_length=20)),
                ('bus_fee', models.DecimalField(default=0.0, max_digits=7, decimal_places=2)),
            ],
        ),
        migrations.AddField(
            model_name='student_rout',
            name='slab',
            field=models.ForeignKey(to='bus_attendance.BusFeeSlab', null=True),
        ),
    ]
