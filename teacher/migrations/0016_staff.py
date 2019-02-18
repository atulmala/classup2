# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0023_auto_20180830_1504'),
        ('teacher', '0015_auto_20180204_1552'),
    ]

    operations = [
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('staff_erp_id', models.CharField(default=b'NA', max_length=30)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(default=b' ', max_length=50, null=True, blank=True)),
                ('email', models.EmailField(default=b'defaultemail@classup.in', max_length=254)),
                ('mobile', models.CharField(max_length=20, null=True)),
                ('active_status', models.BooleanField(default=True)),
                ('school', models.ForeignKey(to='setup.School')),
            ],
            options={
                'ordering': ('first_name',),
            },
        ),
    ]
