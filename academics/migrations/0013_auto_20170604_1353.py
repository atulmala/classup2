# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0012_auto_20170412_1829'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classtest',
            name='test_type',
            field=models.CharField(default=b'Terminal', max_length=200),
        ),
    ]
