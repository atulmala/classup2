# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0023_auto_20180830_1504'),
        ('exam', '0007_npromoted_details'),
    ]

    operations = [
        migrations.CreateModel(
            name='Marksheet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title_start', models.IntegerField(default=120)),
                ('address_start', models.IntegerField(default=145)),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
