# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0014_auto_20170922_1138'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classtest',
            name='test_type',
            field=models.CharField(default=b'unit', max_length=200),
        ),
    ]
