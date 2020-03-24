# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0025_resendsms'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSBatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('batch', models.CharField(max_length=20)),
                ('total', models.IntegerField()),
                ('success', models.IntegerField()),
                ('fail', models.IntegerField()),
            ],
        ),
    ]
