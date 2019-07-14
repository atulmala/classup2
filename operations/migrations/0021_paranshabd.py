# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0020_auto_20190712_1730'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParanShabd',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('upbhokta', models.CharField(max_length=15)),
                ('shabd', models.CharField(max_length=10)),
            ],
        ),
    ]
