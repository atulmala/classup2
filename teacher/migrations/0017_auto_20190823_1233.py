# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0016_staff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messagereceivers',
            name='outcome',
            field=models.TextField(default=b'Awaited', max_length=50),
        ),
        migrations.AlterField(
            model_name='messagereceivers',
            name='status',
            field=models.CharField(max_length=350, null=True),
        ),
    ]
