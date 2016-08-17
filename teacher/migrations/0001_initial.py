# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('teacher_erp_id', models.CharField(unique=True, max_length=20)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('email', models.EmailField(default=b'defaultemail@classup.in', max_length=254)),
                ('mobile', models.CharField(max_length=20, null=True)),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
