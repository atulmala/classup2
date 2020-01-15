# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0027_globalconf_short_link_api'),
        ('erp', '0022_auto_20200113_1027'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransportSlab',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slab', models.CharField(default=b'X', max_length=2)),
                ('amount', models.DecimalField(default=0.0, max_digits=8, decimal_places=2)),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
